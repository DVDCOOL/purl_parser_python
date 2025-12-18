from flask import Flask, render_template, Response, request, jsonify
import redis
import json
import requests
import os
from collections import defaultdict, deque
import threading
import time

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', None),
    decode_responses=True
)

API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = os.getenv('API_PORT', 8080)

# In-memory buffers for real-time updates
log_buffer = deque(maxlen=1000)  # Keep last 1000 log entries

# Lock for thread-safe access to buffers
buffer_lock = threading.Lock()

# Event for notifying SSE clients of new data
update_event = threading.Event()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/packages')
def packages_page():
    return render_template('packages.html')


@app.route('/licenses')
def licenses_page():
    return render_template('licenses.html')


@app.route('/addpurl')
def addpurl_page():
    return render_template('addpurl.html')


# ============================================================================
#                           WEBHOOK ENDPOINTS (NEW)
# ============================================================================
def get_queue_stats():
    """Scan Redis queue and count packages per level"""
    try:
        # Get all items from the queue without popping
        queue_length = redis_client.llen('working_queue')
        
        level_counts = defaultdict(int)
        
        # Sample the queue (if it's huge, you might want to limit this)
        # LRANGE is O(N) so be careful with very large queues
        max_scan = min(queue_length, 10000)  # Limit to avoid blocking
        
        items = redis_client.lrange('working_queue', 0, max_scan - 1)
        
        for item in items:
            try:
                entry = json.loads(item)
                level = entry.get('current_level', 0)
                level_counts[level] += 1
            except json.JSONDecodeError:
                continue
        
        return {
            'total': queue_length,
            'scanned': len(items),
            'levels': dict(level_counts)
        }
    except Exception as e:
        app.logger.error(f"Error scanning queue: {e}")
        return {'total': 0, 'scanned': 0, 'levels': {}}

@app.route('/webhook/log', methods=['POST'])
def webhook_log():
    """Receive log messages from spider via HTTP POST"""
    try:
        data = request.get_json()
        
        with buffer_lock:
            log_entry = {
                'type': 'log',
                'data': {
                    'timestamp': data.get('timestamp'),
                    'level': int(data.get('level', 0)),
                    'log_level': data.get('log_level', 'INFO'),
                    'message': data.get('message')
                }
            }
            log_buffer.append(log_entry)
        
        # Notify SSE clients
        update_event.set()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        app.logger.error(f"Error in log webhook: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
#                           SSE STREAMING ENDPOINT
# ============================================================================

@app.route('/progress-stream')
def progress_stream():
    def event_stream():
        try:
            while True:
                # Get current queue stats
                stats = get_queue_stats()
                
                # Send stats update
                yield f"data: {json.dumps({'type': 'queue_stats', 'data': stats})}\n\n"
                
                # Send any pending logs
                with buffer_lock:
                    temp_logs = []
                    while log_buffer:
                        temp_logs.append(log_buffer.popleft())
                    
                    for log in temp_logs:
                        yield f"data: {json.dumps(log)}\n\n"
                
                # Wait before next scan (adjust interval as needed)
                time.sleep(2)  # Scan every 2 seconds
                
        except GeneratorExit:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')


# ============================================================================
#                           EXISTING API ENDPOINTS
# ============================================================================

@app.route('/api/packages')
def api_packages():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))
    per_page = min(limit, 100)

    try:
        r = requests.get(
            f"http://{API_HOST}:{API_PORT}/get_packages",
            params={"page": page, "per_page": per_page},
            timeout=10
        )
    except Exception as e:
        return jsonify({"packages": [], "page": page, "limit": per_page, "has_next": False, "total_packages": 0})

    if r.status_code != 200:
        return jsonify({"packages": [], "page": page, "limit": per_page, "has_next": False, "total_packages": 0})

    data = r.json()
    packages = data.get("packages", [])

    total_packages = 0
    try:
        rcount = requests.get(f"http://{API_HOST}:{API_PORT}/get_number_of_packages", timeout=5)
        if rcount.status_code == 200:
            total_packages = int(rcount.json().get("number_of_packages", 0))
    except Exception:
        total_packages = 0

    result = []
    for p in packages:
        licenses = [l.get("license") for l in p.get("licenses", [])] if p.get("licenses") else []
        versions = [v.get("version") for v in p.get("versions", [])] if p.get("versions") else []

        description = p.get("description")
        number_of_dependents = p.get("number_of_dependents", len(p.get("dependents", []) if p.get("dependents") else []))

        result.append({
            "ecosystem": p.get("ecosystem"),
            "name": p.get("name"),
            "license": ", ".join(licenses) if licenses else "Unknown",
            "version": versions[0] if versions else None,
            "description": description,
            "number_of_dependents": number_of_dependents
        })

    has_next = len(packages) == per_page and (total_packages == 0 or page * per_page < total_packages)

    return jsonify({
        "packages": result,
        "page": page,
        "limit": per_page,
        "has_next": has_next,
        "total_packages": total_packages
    })


@app.route('/db/licenses')
def api_licenses():
    page = 1
    lic_counts = {}

    while True:
        try:
            r = requests.get(f"http://{API_HOST}:{API_PORT}/get_packages", params={"page": page, "per_page": 100}, timeout=10)
        except Exception:
            break

        if r.status_code != 200:
            break

        pkgs = r.json().get('packages', [])
        if not pkgs:
            break

        for p in pkgs:
            licenses = p.get("licenses", [])
            if not licenses:
                lic = "Unknown"
                lic_counts[lic] = lic_counts.get(lic, 0) + 1
            else:
                for item in licenses:
                    lic = item.get("license") or "Unknown"
                    lic_counts[lic] = lic_counts.get(lic, 0) + 1

        page += 1

    return jsonify({"licenses": lic_counts})


@app.route('/add_purls', methods=['POST'])
def add_purls():
    body = request.get_json()
    text = body.get("purls", "")

    purls = [line.strip() for line in text.split("\n") if line.strip()]

    count = 0
    for p in purls:
        redis_client.lpush("input_queue", p)
        count += 1

    redis_client.lpush("input_queue", "true")

    return jsonify({"status": f"Added {count} PURLs."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('WEBAPP_PORT', 5000)), debug=True)