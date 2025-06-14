
    import re, os, requests
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv
    from openai import OpenAI

    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def clean_url(url: str) -> str:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url.split("#")[0]

    def scrape_website_text(url, max_chars=8000):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = re.sub(r"\s+", " ", soup.get_text(" ").strip())
            return text[:max_chars]
        except Exception as e:
            return f"Error scraping site: {e}"

    def run_memoscan_stream(url: str):
        website_text = scrape_website_text(url)
        print("[DEBUG] First 250 chars scraped:\n", website_text[:250])

        if website_text.startswith("Error scraping"):
            yield f"{website_text}\n"
            return
        if len(website_text) < 100:
            yield "⚠️ Not enough content to evaluate memorability.\n"
            return

        prompt = f"""You are a senior brand consultant using Saffron’s Memorability Framework.

For each key (Emotion, Attention, Story, Involvement, Repetition, Consistency) output ONE line:
Key|Score/10|Short Title|Strategic Explanation (2–4 sentences)

Now analyse:
""" + website_text

        stream = client.chat.completions.create(
            model="gpt-4",
            stream=True,
            messages=[
                {"role": "system", "content": "You are a helpful branding expert."},
                {"role": "user", "content": prompt}
            ],
        )

        buffer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                buffer += delta.content
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        yield line.strip() + "\n"
        if buffer.strip():
            yield buffer.strip() + "\n"
