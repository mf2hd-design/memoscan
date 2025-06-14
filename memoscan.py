# memoscan.py

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MEMORABILITY_KEYS = {
    "Emotion": "Does the brand evoke strong feelings or values? Is there emotional resonance in the messaging?",
    "Attention": "Does the brand capture and hold attention? Is it visually or verbally distinctive?",
    "Story": "Does the brand have a clear and compelling narrative that explains what it stands for?",
    "Involvement": "Does the brand involve the audience? Does it encourage participation, personalization or belonging?",
    "Repetition": "Are key brand elements repeated consistently across touchpoints?",
    "Consistency": "Is the brand identity coherent and uniform across messages, tone, and visuals?"
}

def scrape_website_text(url, max_chars=3000):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception as e:
        return f"Error scraping site: {e}"

def run_memoscan_stream(url):
    brand_text = scrape_website_text(url)
    for key, description in MEMORABILITY_KEYS.items():
        prompt = f"""
You are a senior brand strategist evaluating a brand’s memorability based on the key: **{key}**.

Instructions:
1. Apply this lens: "{description}"
2. Score the brand from 0–100.
3. Justify your score in 2–3 bullet points.
Only reply with your score and bullet points. Do not repeat the prompt or restart.

Website content:
\"\"\"{brand_text}\"\"\"
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content.strip()

        # SSE message
        yield f"data: {json.dumps({'key': key, 'result': result})}\n\n"

    # Signal that the scan is done
    yield "event: end\ndata: done\n\n"
