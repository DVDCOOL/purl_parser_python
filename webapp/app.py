from flask import Flask, render_template, Response, request, jsonify
import redis
import json
import requests
import os
from collections import defaultdict

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

level_states = defaultdict(dict)


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


@app.route('/progress-stream')
def progress_stream():
    def event_stream():
        yield f"data: {json.dumps({'type': 'init', 'levels': dict(level_states)})}\n\n"

        try:
            last_progress_id = '$'
            last_log_id = '$'

            while True:
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

                if progress_messages:
                    for stream, msgs in progress_messages:
                        for msg_id, fields in msgs:
                            try:
                                level = int(fields['level'])
                            except Exception:
                                level = 0

                            levels_to_remove = [l for l in level_states.keys() if l > level]
                            for l in levels_to_remove:
                                del level_states[l]

                            level_states[level] = {
                                'timestamp': fields.get('timestamp'),
                                'package': fields.get('package'),
                                'dependent_idx': int(fields.get('dependent_idx', 0)),
                                'total_dependents': int(fields.get('total_dependents', 0)),
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

                if log_messages:
                    for stream, msgs in log_messages:
                        for msg_id, fields in msgs:
                            log_update = {
                                'type': 'log',
                                'data': {
                                    'timestamp': fields.get('timestamp'),
                                    'level': int(fields.get('level', 0)),
                                    'log_level': fields.get('log_level', 'INFO'),
                                    'message': fields.get('message')
                                }
                            }
                            yield f"data: {json.dumps(log_update)}\n\n"
                            last_log_id = msg_id

                if not progress_messages and not log_messages:
                    yield f": heartbeat\n\n"

        except GeneratorExit:
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')


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