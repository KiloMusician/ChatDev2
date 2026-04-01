from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/v1/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt") or data.get("input") or ""
    # Minimal mock: echo prompt and return a deterministic 'response'
    resp = {
        "model": data.get("model", "mock-ollama"),
        "prompt": prompt,
        "response": f"MOCK_RESPONSE: {prompt[:200]}",
        "ok": True,
    }
    return jsonify(resp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
