import os
import time
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

MEMORABILITY_KEYS = [
    "Emotional Impact",
    "Attention",
    "Clarity",
    "Involvement",
    "Repetition",
    "Consistency"
]

def clean_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url

def scrape_website_text(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text[:10000]  # Trim to 10,000 chars for safety
    except Exception as e:
        return f"Error fetching website: {str(e)}"

def run_memoscan_stream(url):
    url = clean_url(url)
    page_text = scrape_website_text(url)

    prompt = f"""
You are a brand strategist. Analyze the following website content and score it on 6 memorability keys:
1. Emotional Impact
2. Attention
3. Clarity
4. Involvement
5. Repetition
6. Consistency

Each score should be out of 10, followed by 1-2 sentences of explanation. Return the results **one at a time**, in the format:
Key|Score|Explanation

Website content:
\"\"\"
{page_text}
\"\"\"
    """

    stream = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        stream=True
    )

    for chunk in stream:
        if not chunk.choices or not chunk.choices[0].delta.get("content"):
            continue
        line = chunk.choices[0].delta.content
        if "|" in line:
            yield line.strip()
