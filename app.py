from flask import Flask, render_template, request, Response
from memoscan import run_memoscan_stream
from urllib.parse import urlparse
import os

app = Flask(__name__)

def clean_url(raw_url):
    """Ensure the URL is valid and prepend scheme if missing."""
    parsed = urlparse(raw_url)
    if not parsed.scheme:
        raw_url = 'https://' + raw_url
    return raw_url

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan")
def scan():
    raw_url = request.args.get("url", "")
    cleaned_url = clean_url(raw_url)

    def generate():
        for result in run_memoscan_stream(cleaned_url):
            # Debug log (optional, remove in production)
            print("YIELD:", result)

            # Handle if result is a string like "Key|Score|Explanation"
            if isinstance(result, str):
                try:
                    parts = result.split("|")
                    key = parts[0].strip()
                    score = parts[1].strip()
                    explanation = parts[2].strip() if len(parts) > 2 else "No explanation."
                except Exception:
                    key = "Parse Error"
                    score = "?"
                    explanation = f"Could not parse result: {result}"
            # Handle if result is a dictionary
            elif isinstance(result, dict):
                key = result.get("key", "Unknown Key")
                score = result.get("score", "?")
                explanation = result.get("explanation", "No explanation provided.")
            else:
                key = "Invalid Result"
                score = "?"
                explanation = str(result)

            block = f"""
            <div class='result-block'>
                <h2>{key}: <span class='score'>{score}/10</span></h2>
                <p>{explanation}</p>
            </div>
            """
            yield f"data: {block}\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
