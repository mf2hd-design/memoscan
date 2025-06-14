
from flask import Flask, render_template, request, Response
from memoscan import run_memoscan_stream, clean_url

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan")
def scan():
    url = request.args.get("url", "").strip()
    cleaned = clean_url(url)
    print(f"[DEBUG] /scan requested for: {cleaned}")

    def generate():
        try:
            for line in run_memoscan_stream(cleaned):
                yield f"data: {line}\n\n"
        except Exception as e:
            print("[ERROR] Streaming failure:", e)
            yield f"data: ⚠️ Internal error: {e}\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
