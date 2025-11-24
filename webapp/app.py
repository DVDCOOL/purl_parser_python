from flask import Flask, render_template, Response
import redis
import json
import time
from collections import defaultdict

app = Flask(__name__)

# Redis connection (from .env in docker-compose)
import os
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', None),
    decode_responses=True
)

level_states = defaultdict(dict)  # {level: {timestamp, package, progress}}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress-stream')
def progress_stream():
    def event_stream():
        # First, send ALL current level states
        yield f"data: {json.dumps({'type': 'init', 'levels': dict(level_states)})}\n\n"
        
        # Then listen for new updates
        try:
            # Start reading from NOW (don't replay old entries)
            streams = {'spider:progress': '$'}
            
            while True:
                messages = redis_client.xread(streams, block=1000, count=10)
                
                if messages:
                    for stream, msgs in messages:
                        for msg_id, fields in msgs:
                            level = int(fields['level'])
                            
                            # UPDATE the persistent state for this level
                            level_states[level] = {
                                'timestamp': fields['timestamp'],
                                'package': fields['package'],
                                'dependent_idx': int(fields['dependent_idx']),
                                'total_dependents': int(fields['total_dependents']),
                                'page': int(fields.get('page', 1))
                            }
                            
                            # Calculate display values
                            display_idx = level_states[level]['dependent_idx'] + (level_states[level]['page'] - 1) * 100
                            display_total = level_states[level]['total_dependents'] + (level_states[level]['page'] - 1) * 100
                            
                            # Send update to browser
                            update = {
                                'type': 'update',
                                'level': level,
                                'data': {
                                    'timestamp': level_states[level]['timestamp'],
                                    'progress': f"{display_idx}/{display_total}",
                                    'package': level_states[level]['package']
                                }
                            }
                            yield f"data: {json.dumps(update)}\n\n"
                            
                            # Update stream position
                            streams['spider:progress'] = msg_id
                        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('WEBAPP_PORT', 8080)), debug=True)