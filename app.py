# app.py

from flask import Flask, render_template, request, Response
from memoscan import run_memoscan_stream

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    raw_url = request.args.get("url", "").strip()

    # Normalize user input to include https:// if missing
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        url = "https://" + raw_url
    else:
        url = raw_url

    return Response(run_memoscan_stream(url), mimetype="text/event-stream")

if __name__ == "__main__":
import os

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port, debug=True)
