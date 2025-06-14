import os
import warnings
import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# 🧼 Suppress SSL warning on Mac with LibreSSL
warnings.filterwarnings("ignore", category=UserWarning)

# 🔑 Load OpenAI API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 📌 Define the Six Memorability Keys
MEMORABILITY_KEYS = {
    "Emotion": "Does the brand evoke strong feelings or values? Is there emotional resonance in the messaging?",
    "Attention": "Does the brand capture and hold attention? Is it visually or verbally distinctive?",
    "Story": "Does the brand have a clear and compelling narrative that explains what it stands for?",
    "Involvement": "Does the brand involve the audience? Does it encourage participation, personalization or belonging?",
    "Repetition": "Are key brand elements repeated consistently across touchpoints?",
    "Consistency": "Is the brand identity coherent and uniform across messages, tone, and visuals?"
}

# 🌐 Scrape website content
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

# 🏁 Define which brand to scan
brand_url = "https://www.nvidia.com"  # Try replacing with any brand
brand_text = scrape_website_text(brand_url)

# 📊 Store results
results = {}

# 🔁 Run analysis for each memorability key
for key, description in MEMORABILITY_KEYS.items():
    prompt = f"""
You are a senior brand strategist evaluating a brand’s memorability based on the key: **{key}**.

Instructions:
1. Read the website content below.
2. Apply this memorability lens: "{description}"
3. Score the brand from 0 to 100 on this key.
4. Justify your score in 2-3 bullet points.
5. Be critical but constructive.

Website content:
\"\"\"
{brand_text}
\"\"\"
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    results[key] = result

    print(f"\n🟠 {key} Score:\n{result}\n{'-'*60}")

# 💾 Save to JSON
with open("memoscan_scores.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n✅ Memorability scan complete. Results saved to memoscan_scores.json")