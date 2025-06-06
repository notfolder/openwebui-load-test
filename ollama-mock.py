import time
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

DUMMY_TEXT = "この応答はダミーの応答です。10回繰り返したら終わり。\n適当な長さの応答があれば良い。"

# /api/generate (streaming)
@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json(force=True)
    stream = data.get('stream', True)
    model = data.get('model', 'dummy')
    if stream:
        def generate_stream():
            for i in range(10):
                yield f'{ {"model": model, "done": False, "response": DUMMY_TEXT, "count": i+1} }\n'
                time.sleep(1)
            yield f'{ {"model": model, "done": True, "response": DUMMY_TEXT, "count": 10} }\n'
        return Response(generate_stream(), mimetype='application/json')
    else:
        return jsonify({
            "model": model,
            "done": True,
            "response": DUMMY_TEXT * 10,
            "count": 10
        })

# /api/chat (streaming, NDJSON)
@app.route('/api/chat', methods=['POST'])
def api_chat():
    import json
    data = request.get_json(force=True)
    stream = data.get('stream', True)
    model = data.get('model', 'dummy')
    if stream:
        def chat_stream():
            for i in range(10):
                chunk = {
                    "model": model,
                    "done": False,
                    "message": {"role": "assistant", "content": DUMMY_TEXT},
                    "count": i+1
                }
                yield json.dumps(chunk) + "\n"
                time.sleep(1)
            last_chunk = {
                "model": model,
                "done": True,
                "message": {"role": "assistant", "content": DUMMY_TEXT},
                "count": 10,
                "eval_duration": 1000000000
            }
            yield json.dumps(last_chunk) + "\n"
        return Response(chat_stream(), mimetype='application/x-ndjson')
    else:
        return jsonify({
            "model": model,
            "done": True,
            "message": {"role": "assistant", "content": DUMMY_TEXT * 10},
            "count": 10,
            "eval_duration": 1000000000
        })

# /api/create
@app.route('/api/create', methods=['POST'])
def api_create():
    def create_stream():
        yield '{"status":"reading model metadata"}\n'
        time.sleep(0.2)
        yield '{"status":"creating system layer"}\n'
        time.sleep(0.2)
        yield '{"status":"writing manifest"}\n'
        time.sleep(0.2)
        yield '{"status":"success"}\n'
    return Response(create_stream(), mimetype='application/json')

# /api/tags
@app.route('/api/tags', methods=['GET'])
def api_tags():
    return jsonify({
        "models": [
            {
                "name": "dummy:latest",
                "model": "dummy:latest",
                "size": 123456,
                "digest": "sha256:dummy",
                "modified_at": "2024-01-01T00:00:00Z"
            }
        ]
    })

# /api/show
@app.route('/api/show', methods=['POST'])
def api_show():
    data = request.get_json(force=True)
    model = data.get('model', 'dummy')
    return jsonify({
        "modelfile": f"# Modelfile for {model}",
        "details": {"name": model, "size": 123456},
        "template": "{{ .System }}\nUSER: {{ .Prompt }}\nASSISTANT: ",
        "parameters": {"num_ctx": 4096},
        "license": "dummy-license",
        "system": "dummy system prompt"
    })

# /api/copy
@app.route('/api/copy', methods=['POST'])
def api_copy():
    return jsonify({"status": "ok"})

# /api/delete
@app.route('/api/delete', methods=['DELETE'])
def api_delete():
    return jsonify({"status": "ok"})

# /api/pull
@app.route('/api/pull', methods=['POST'])
def api_pull():
    def pull_stream():
        yield '{"status":"downloading"}\n'
        time.sleep(0.2)
        yield '{"status":"success"}\n'
    return Response(pull_stream(), mimetype='application/json')

# /api/blobs/:digest (HEAD)
@app.route('/api/blobs/<digest>', methods=['HEAD'])
def api_blobs_head(digest):
    # Always return 200 OK for mock
    return ('', 200)

# /api/blobs/:digest (POST)
@app.route('/api/blobs/<digest>', methods=['POST'])
def api_blobs_post(digest):
    # Accept file upload, always return 201 Created
    return ('', 201)

@app.route('/')
def index():
    return 'Ollama API Mock is running.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11434)
