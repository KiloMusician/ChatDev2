import logging
import requests  # type: ignore[import-untyped]
from flask import Flask, send_from_directory, request, jsonify
try:
    import telemetry.tracing_setup as tracing
except ModuleNotFoundError:
    import tracing_setup as tracing
import argparse
from typing import List, Dict

app = Flask(__name__, static_folder="static")
app.logger.setLevel(logging.ERROR)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
messages: List[Dict[str, str]] = []  # type: ignore[assignment]
port = [8000]

# Initialize optional tracing for the visualizer (no-op if OTEL not installed)
tracer = tracing.initialize_tracing(service_name="chatdev_visualizer")
tracing.instrument_requests()
tracing.instrument_flask(app)


def send_msg(role: str, text: str) -> None:
    """Send a message to the local visualization server with a safe timeout.

    This function is best-effort; failures are logged but not raised.
    """
    try:
        with tracing.start_span("send_msg", {"role": role}):
            data = {"role": role, "text": text}
            # Short timeout prevents indefinite hang if server not yet started.
            post_url = f"http://127.0.0.1:{port[-1]}/send_message"
            _ = requests.post(post_url, json=data, timeout=5)
    except (OSError, requests.RequestException, ValueError) as e:
        logging.warning("Visualization server not reachable: %s", e)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/chain_visualizer")
def chain_visualizer():
    return send_from_directory("static", "chain_visualizer.html")


@app.route("/replay")
def replay():
    return send_from_directory("static", "replay.html")


@app.route("/get_messages")
def get_messages():
    return jsonify(messages)


@app.route("/send_message", methods=["POST"])
def send_message():
    with tracing.start_span("send_message"):
        data = request.get_json() or {}
    role = data.get("role", "unknown")
    text = data.get("text", "")

    avatar_url = find_avatar_url(role)

    message = {"role": role, "text": text, "avatarUrl": avatar_url}
    messages.append(message)
    return jsonify(message)


def find_avatar_url(role: str) -> str:
    sanitized = role.replace(" ", "%20")
    avatar_filename = f"avatars/{sanitized}.png"
    return f"/static/{avatar_filename}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatDev Visualizer Server")
    parser.add_argument(
        "--port", type=int, default=8000, help="Serve port (default 8000)"
    )
    args = parser.parse_args()
    port.append(args.port)
    logging.info(
        "UI: http://127.0.0.1:%s/ (use --port for alt)",
        port[-1],
    )
    app.run(host="0.0.0.0", debug=False, port=port[-1])
