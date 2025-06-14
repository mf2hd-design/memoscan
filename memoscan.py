import requests
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def scrape_website_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for script in soup(["script", "style", "noscript"]):
            script.decompose()

        text = soup.get_text(separator=' ')
        cleaned_text = re.sub(r'\s+', ' ', text).strip()
        return cleaned_text[:8000]  # Truncate for token limit
    except Exception as e:
        return f"Error scraping site: {e}"

def run_memoscan_stream(url):
    website_text = scrape_website_text(url)

    prompt = f"""
You are a senior brand strategist at Saffron. Use Saffron’s Memorability Framework to evaluate how memorable the brand is based on this scraped website content. Assess it using the six keys of memorability:

1. **Emotion** – What level of emotion does the brand evoke?
   - Does it create warmth, admiration, joy, excitement, trust?

2. **Attention** – How well does the brand capture and sustain attention?
   - Does the content surprise, intrigue, or feel distinctive?

3. **Story** – What kind of story does the brand tell?
   - Is it coherent, meaningful, and appealing?
   - Can the audience quickly grasp what the brand stands for?

4. **Involvement** – How good is the brand at involving people?
   - Does it invite interaction, shared purpose, or participation?

5. **Repetition** – How often does the brand repeat important elements?
   - Are phrases, visuals, or themes reused to reinforce recall?

6. **Consistency** – How consistently are the brand’s core elements used?
   - Are tone, layout, visuals, and story aligned across the experience?

---

Evaluate each of these six keys. For each one, provide:
- A score from 1–10
- A short headline
- A strategic explanation (3–4 sentences). Explain what works, what doesn’t, and how to improve.

Return the results in **JSON** format using this exact structure:

[
  {{
    "key": "Emotion",
    "score": 6,
    "title": "Some Warmth, Some Distance",
    "explanation": "The brand conveys professionalism and care through its visuals, but the language remains fairly neutral. Emotional triggers are limited. Greater storytelling or human-focused language could elevate the emotional resonance."
  }},
  ...
]

Now assess this content:

\"\"\"{website_text}\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4",
        stream=True,
        messages=[
            {"role": "system", "content": "You are a thoughtful, critical brand strategist."},
            {"role": "user", "content": prompt}
        ]
    )

    for chunk in response:
        if hasattr(chunk.choices[0].delta, "content"):
            yield chunk.choices[0].delta.content

def clean_url(url: str) -> str:
    """Ensures the URL starts with https:// and strips whitespace."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url
