from flask import Flask, render_template, request, Response
from memoscan import run_memoscan_stream, clean_url

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan")
def scan():
    url = request.args.get("url", "")
    cleaned_url = clean_url(url)

    def generate():
        try:
            for result in run_memoscan_stream(cleaned_url):
                try:
                    key, score, explanation = result.split("|", 2)
                except ValueError:
                    yield f"data: <div class='result-block'>⚠️ Invalid format: {result}</div>\n\n"
                    continue

                html_block = (
                    f"<div class='result-block'>"
                    f"<div><strong>{key}</strong>: <span class='score'>{score}/10</span></div>"
                    f"<div style='white-space: pre-wrap; margin-top: 5px;'>{explanation}</div>"
                    f"</div>"
                )
                yield f"data: {html_block}\n\n"
        except Exception as e:
            yield f"data: <div class='result-block error'>⚠️ Internal error: {str(e)}</div>\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
