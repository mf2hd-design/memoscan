import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

MEMORABILITY_KEYS = [
    {"name": "Emotional Impact", "description": "Does the brand message connect emotionally with its audience?"},
    {"name": "Attention", "description": "How well does the brand attract and sustain attention?"},
    {"name": "Clarity", "description": "Is the brand’s story clear and easy to understand?"},
    {"name": "Involvement", "description": "Does the brand make the audience feel involved or engaged?"},
    {"name": "Repetition", "description": "Are key brand elements repeated consistently across touchpoints?"},
    {"name": "Consistency", "description": "Are visuals, tone, and messages aligned and coherent?"}
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
        return text[:10000]  # Limit to 10,000 characters
    except Exception as e:
        return f"Error fetching website: {str(e)}"

def run_memoscan_stream(url):
    url = clean_url(url)
    page_text = scrape_website_text(url)

    prompt = f"""
You are a senior brand strategist at a global branding consultancy.
Your task is to evaluate the memorability of the website content provided below.

Score the content from 1 to 10 for each of the following six keys of memorability:

1. Emotional Impact — Does the brand message connect emotionally with its audience?
2. Attention — How well does the brand attract and sustain attention?
3. Clarity — Is the brand’s story clear and easy to understand?
4. Involvement — Does the brand make the audience feel involved or engaged?
5. Repetition — Are key brand elements repeated consistently across touchpoints?
6. Consistency — Are visuals, tone, and messages aligned and coherent?

Return your output in **exactly** this format, one line at a time:

Key|Score|Explanation

For example:
Clarity|8|The message is clearly structured and easy to understand, with intuitive navigation.

Now begin your analysis of the following website content:
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

    buffer = ""
    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            buffer += delta.content
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if "|" in line and line.count("|") == 2:
                    yield line
