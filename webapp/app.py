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
level_states = defaultdict(dict)
log_buffer = deque(maxlen=1000)  # Keep last 1000 log entries
progress_buffer = deque(maxlen=100)  # Keep last 100 progress updates

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

@app.route('/webhook/progress', methods=['POST'])
def webhook_progress():
    """Receive progress updates from spider via HTTP POST"""
    try:
        data = request.get_json()
        
        level = int(data.get('level', 0))
        timestamp = data.get('timestamp')
        package = data.get('package')
        dependent_idx = int(data.get('dependent_idx', 0))
        total_dependents = int(data.get('total_dependents', 0))
        page = int(data.get('page', 1))
        
        with buffer_lock:
            # Clear higher levels when we go back to a lower level
            levels_to_remove = [l for l in level_states.keys() if l > level]
            for l in levels_to_remove:
                del level_states[l]
            
            # Update current level state
            level_states[level] = {
                'timestamp': timestamp,
                'package': package,
                'dependent_idx': dependent_idx,
                'total_dependents': total_dependents,
                'page': page
            }
            
            # Add to progress buffer for SSE streaming
            progress_buffer.append({
                'type': 'progress',
                'level': level,
                'removed_levels': levels_to_remove,
                'data': {
                    'timestamp': timestamp,
                    'progress': f"{dependent_idx}/{total_dependents}",
                    'package': package,
                    'page': page
                }
            })
        
        # Notify SSE clients
        update_event.set()
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        app.logger.error(f"Error in progress webhook: {e}")
        return jsonify({'error': str(e)}), 500


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
        # Send initial state
        with buffer_lock:
            yield f"data: {json.dumps({'type': 'init', 'levels': dict(level_states)})}\n\n"
            
            # Send recent logs
            for log in list(log_buffer):
                yield f"data: {json.dumps(log)}\n\n"

        try:
            while True:
                # Wait for new updates (with timeout for heartbeat)
                update_event.wait(timeout=30)
                update_event.clear()
                
                # Send all pending updates
                with buffer_lock:
                    # Send progress updates
                    while progress_buffer:
                        update = progress_buffer.popleft()
                        yield f"data: {json.dumps(update)}\n\n"
                    
                    # Send log updates
                    temp_logs = []
                    while log_buffer and len(temp_logs) < 10:  # Send max 10 logs at once
                        temp_logs.append(log_buffer.popleft())
                    
                    for log in temp_logs:
                        yield f"data: {json.dumps(log)}\n\n"
                
                # Heartbeat (if no updates were sent)
                if not temp_logs and not progress_buffer:
                    yield f": heartbeat\n\n"

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
        redis_client.lpush("waiting_room", p)
        count += 1

    redis_client.lpush("waiting_room", "true")

    return jsonify({"status": f"Added {count} PURLs."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('WEBAPP_PORT', 5000)), debug=True)