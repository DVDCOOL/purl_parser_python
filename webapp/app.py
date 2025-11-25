from flask import Flask, render_template, Response, request, jsonify
import redis
import json
import requests
import os
from collections import defaultdict

app = Flask(__name__)

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', None),
    decode_responses=True
)

API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = os.getenv('API_PORT', 8080)

level_states = defaultdict(dict)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/progress-stream')
def progress_stream():
    def event_stream():
        # Send initial state
        yield f"data: {json.dumps({'type': 'init', 'levels': dict(level_states)})}\n\n"
        
        try:
            # Start reading from NOW for both streams
            last_progress_id = '$'
            last_log_id = '$'
            
            while True:
                # Read from both streams separately
                progress_messages = redis_client.xread(
                    {'spider:progress': last_progress_id}, 
                    block=500, 
                    count=10
                )
                
                log_messages = redis_client.xread(
                    {'spider:logs': last_log_id}, 
                    block=500, 
                    count=10
                )
                
                # Process progress updates
                if progress_messages:
                    for stream, msgs in progress_messages:
                        for msg_id, fields in msgs:
                            level = int(fields['level'])
                            
                            levels_to_remove = [l for l in level_states.keys() if l > level]
                            for l in levels_to_remove:
                                del level_states[l]
                            
                            level_states[level] = {
                                'timestamp': fields['timestamp'],
                                'package': fields['package'],
                                'dependent_idx': int(fields['dependent_idx']),
                                'total_dependents': int(fields['total_dependents']),
                                'page': int(fields.get('page', 1))
                            }
                            
                            page = level_states[level]['page']
                            idx = level_states[level]['dependent_idx']
                            total = level_states[level]['total_dependents']
                            
                            items_per_page = 100
                            global_idx = idx + (page - 1) * items_per_page
                            global_total = total + (page - 1) * items_per_page
                            
                            update = {
                                'type': 'progress',
                                'level': level,
                                'removed_levels': levels_to_remove,
                                'data': {
                                    'timestamp': level_states[level]['timestamp'],
                                    'progress': f"{global_idx}/{global_total}",
                                    'package': level_states[level]['package'],
                                    'page': page
                                }
                            }
                            yield f"data: {json.dumps(update)}\n\n"
                            last_progress_id = msg_id
                
                # Process log updates
                if log_messages:
                    for stream, msgs in log_messages:
                        for msg_id, fields in msgs:
                            log_update = {
                                'type': 'log',
                                'data': {
                                    'timestamp': fields['timestamp'],
                                    'level': int(fields['level']),
                                    'log_level': fields.get('log_level', 'INFO'),
                                    'message': fields['message']
                                }
                            }
                            yield f"data: {json.dumps(log_update)}\n\n"
                            last_log_id = msg_id
                
                # Send heartbeat if no messages (keeps connection alive)
                if not progress_messages and not log_messages:
                    yield f": heartbeat\n\n"
                        
        except GeneratorExit:
            # Client disconnected
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api/packages')
def api_packages():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 100))  # default 100

    r = requests.get(
        f"http://{API_HOST}:{API_PORT}/get_packages?page={page}&limit={limit}"
    )

    if r.status_code != 200:
        return jsonify({"packages": [], "page": page, "has_next": False})

    data = r.json()
    packages = data.get("packages", [])

    # Prepare simplified fields for UI
    result = []
    for p in packages:
        licenses = [l.get("license") for l in p.get("licenses", [])]
        versions = [v.get("version") for v in p.get("versions", [])]

        result.append({
            "ecosystem": p.get("ecosystem"),
            "name": p.get("name"),
            "license": ", ".join(licenses) if licenses else "Unknown",
            "version": versions[0] if versions else None,
        })

    # Detect if we have more pages
    has_next = len(packages) == limit

    return jsonify({
        "packages": result,
        "page": page,
        "limit": limit,
        "has_next": has_next,
    })



@app.route('/db/licenses')
def api_licenses():
    page = 1
    lic_counts = {}

    while True:
        r = requests.get(f"http://{API_HOST}:{API_PORT}/get_packages?page={page}")
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
    app.run(host='0.0.0.0', port=int(os.getenv('WEBAPP_PORT', 8080)), debug=True)