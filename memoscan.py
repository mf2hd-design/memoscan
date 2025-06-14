import requests
from bs4 import BeautifulSoup
import re
import os
from openai import OpenAI
from dotenv import load_dotenv

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
        return cleaned_text[:8000]  # Truncate for token safety
    except Exception as e:
        return f"Error scraping site: {e}"

def clean_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url

def run_memoscan_stream(website_text):
    prompt = """
You are a senior brand consultant using Saffron’s Memorability Framework to evaluate how memorable a brand is based on its website content.

Saffron’s research shows that brands which score highly on these six keys are more likely to be chosen quickly, remembered over time, and preferred at a premium. Your job is to help the brand understand where it stands — and how to improve.

Evaluate the brand using the six keys below. For each one, provide:
- A score from 1 to 10
- A short title summarizing the result
- A strategic explanation: what’s working, what’s not, and how memorability can be improved

The six keys are:

1. **Emotion** – What level of emotion does the brand evoke?
   - Does it trigger emotional reactions or is it purely factual?
   - Does the tone create connection, warmth, trust, admiration, or excitement?

2. **Attention** – How well does the brand capture and sustain attention?
   - Does the content and story surprise, intrigue, or feel distinctive?
   - Is there a creative spark or hook that keeps people engaged?

3. **Story** – What kind of story does the brand tell?
   - Is the story coherent, meaningful, and appealing?
   - Does it help the audience quickly understand what the brand stands for?

4. **Involvement** – How good is the brand at involving people?
   - Does it invite participation, interaction, or shared purpose?
   - Does the brand treat the audience as part of its world?

5. **Repetition** – How often does the brand repeat important elements throughout the experience?
   - Are there recognisable phrases, messages, or visuals used consistently?

6. **Consistency** – How consistently does the brand use its most important elements?
   - Are tone, design, and story aligned across the pages and touchpoints?
   - Does it feel coherent and familiar at every interaction?

---

Output each rating exactly using this format on a separate line:

Key | Score/10 | Short Title | Strategic Explanation (2–4 sentences)

Now evaluate the following website content:
""" + website_text

    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant and strategic branding expert."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    buffer = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            buffer += delta.content
            if "\n" in buffer:
                lines = buffer.split("\n")
                for line in lines[:-1]:
                    line = line.strip()
                    if line:
                        yield f"<div class='result-block'>{line}</div>"
                buffer = lines[-1]

    if buffer.strip():
        yield f"<div class='result-block'>{buffer.strip()}</div>"
