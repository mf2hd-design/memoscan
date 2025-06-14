import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- helpers ----------
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

# ---------- streaming ----------
def run_memoscan_stream(url: str):
    website_text = scrape_website_text(url)
    print("[DEBUG] First 200 chars scraped:\n", website_text[:200])

    # Early‐exit fall-backs
    if website_text.startswith("Error scraping"):
        yield f"{website_text}\n"
        return
    if len(website_text) < 100:
        yield "⚠️ Not enough content to evaluate memorability.\n"
        return

    prompt = f"""
You are a senior brand consultant at Saffron. 
Evaluate this website using Saffron’s Memorability Framework.

For **each key** provide:
• Score 1–10  
• Short title (headline)  
• Strategic explanation (≈3 sentences): what's working, what's missing, and how to improve.

Return **six lines only**, each in the format:
Key|Score/10|Short Title|Strategic Explanation

—— THE SIX KEYS & WHAT TO MEASURE ——  
1. **Emotion** – Does the content evoke positive feelings (warmth, trust, excitement, admiration)? Assess imagery, tone of voice, word choice, and storytelling techniques that stimulate emotion.  
2. **Attention** – Does the site instantly capture attention and sustain interest? Judge distinctiveness, surprising elements, pacing, and creative hooks.  
3. **Story** – Is there a clear, coherent narrative that conveys purpose and values? Measure clarity of message hierarchy, brand origin, and future vision.  
4. **Involvement** – How well does the brand invite interaction or make the audience feel part of a community? Look for calls-to-action, interactive features, or inclusive language.  
5. **Repetition** – Are key visual, verbal, or thematic elements reused to reinforce recall? Evaluate repeated slogans, colour cues, typography, or sound cues across the page.  
6. **Consistency** – Are design, tone, and messaging aligned across sections, creating a familiar and trustworthy experience? Check layout grids, typography hierarchy, imagery style, and tonal coherence.  

🔑 Output exactly six lines—no extra commentary or blank lines.

Website content to analyse:
\"\"\"{website_text}\"\"\"
"""

    stream = client.chat.completions.create(
        model="gpt-4",
        stream=True,
        messages=[
            {"role": "system", "content": "You are a concise but insightful branding expert."},
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
