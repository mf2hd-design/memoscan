import os, re, requests, json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TWITTER_BEARER   = os.getenv("TWITTER_BEARER_TOKEN")
LINKEDIN_TOKEN   = os.getenv("LINKEDIN_ACCESS_TOKEN")   # needs r_organization_social scope

# -----------------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------------
def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.split("#")[0]

def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ").strip())

def _same_domain(home: str, test: str) -> bool:
    return urlparse(home).netloc == urlparse(test).netloc

# -----------------------------------------------------------------------------------
# Crawl up to 5 pages in-domain
# -----------------------------------------------------------------------------------
def crawl_site(start_url: str, max_pages: int = 5, max_chars: int = 12000):
    visited, queue, text = set(), [clean_url(start_url)], ""
    social = {"twitter": None, "linkedin": None}

    while queue and len(visited) < max_pages and len(text) < max_chars:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            res.raise_for_status()
            page_text  = _visible_text(res.text)
            text      += " " + page_text

            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"].split("#")[0])
                if _same_domain(start_url, link) and link not in visited and link not in queue:
                    queue.append(link)
                if not social["twitter"] and "twitter.com" in link:
                    m = re.search(r"twitter\\.com/([A-Za-z0-9_]{1,15})", link)
                    if m: social["twitter"] = m.group(1)
                if not social["linkedin"] and "linkedin.com/company" in link:
                    m = re.search(r"linkedin\\.com/company/([A-Za-z0-9\\-]+)", link)
                    if m: social["linkedin"] = m.group(1)
        except Exception as e:
            print("[WARN] skip", url, e)

    return text[:max_chars], social

# -----------------------------------------------------------------------------------
# Social pulls
# -----------------------------------------------------------------------------------
def fetch_recent_tweets(handle: str, n=5):
    if not (TWITTER_BEARER and handle): return ""
    try:
        q = f"https://api.twitter.com/2/tweets/search/recent?query=from:{handle}&max_results={n}&tweet.fields=text"
        r = requests.get(q, headers={"Authorization": f"Bearer {TWITTER_BEARER}"}, timeout=10)
        r.raise_for_status()
        tweets = " ".join(t["text"] for t in r.json().get("data", []))
        print(f"[DEBUG] tweets @{handle}: {len(tweets)} chars")
        return tweets
    except Exception as e:
        print("[WARN] tweet fetch:", e)
        return ""

def fetch_linkedin_posts(slug: str, n=5):
    if not (LINKEDIN_TOKEN and slug): return ""
    try:
        hdr = {"Authorization": f"Bearer {LINKEDIN_TOKEN}"}
        org = requests.get(
            f"https://api.linkedin.com/v2/organizations?q=vanityName&vanityName={slug}",
            headers=hdr, timeout=10).json()
        org_urn = org["elements"][0]["organization"]["~id"]
        posts = requests.get(
            f"https://api.linkedin.com/v2/shares?q=owners&owners=urn:li:organization:{org_urn}&sharesPerOwner={n}",
            headers=hdr, timeout=10).json()
        texts = " ".join(p["text"]["text"] for p in posts.get("elements", []) if p.get("text"))
        print(f"[DEBUG] LinkedIn {slug}: {len(texts)} chars")
        return texts
    except Exception as e:
        print("[WARN] LinkedIn fetch:", e)
        return ""

# -----------------------------------------------------------------------------------
# Main streamer
# -----------------------------------------------------------------------------------
def run_memoscan_stream(start_url: str):
    corpus, social = crawl_site(start_url)
    if social["twitter"]:
        corpus += " " + fetch_recent_tweets(social["twitter"])
    if social["linkedin"]:
        corpus += " " + fetch_linkedin_posts(social["linkedin"])

    if len(corpus) < 150:
        yield "⚠️ Not enough content to evaluate memorability.\n"
        return

    prompt = f"""
You are a senior brand strategist at Saffron Brand Consultants.

Evaluate the brand with Saffron’s Memorability Framework.  
For **each key** provide ONE line in this exact format:  
Key|Score/10|Short Title|Strategic Explanation (≈3 sentences)

———————— MEMORABILITY KEYS & DETAILED CRITERIA ————————  
1. **Emotion** – Does the content evoke warmth, trust, joy, admiration, or excitement?  
   • imagery & colour mood  • narrative tone  • human stories / social proof  
2. **Attention** – How distinctive and arresting is the first impression, and does it sustain interest?  
   • headline hooks  • unique visuals  • movement / pacing  • element of surprise  
3. **Story** – Is there a clear, coherent narrative explaining who the brand is, why it exists, and its promise?  
   • mission / purpose clarity  • “about” storyline  • future vision  • proof-points / case stories  
4. **Involvement** – How well does the brand invite participation or make the audience feel part of a community?  
   • calls-to-action  • interactive elements  • community features  • inclusive language  
5. **Repetition** – Are key verbal, visual, or experiential signals consistently reused so they become sticky?  
   • logo usage  • colour / typography  • repeated tag-lines / slogans  • mnemonic devices  
6. **Consistency** – Does every page and social post align in tone, message, and design, creating familiarity?  
   • grid & layout uniformity  • voice consistency  • imagery style  • seamless cross-channel experience  

ONLY output those six lines, nothing else.

————— BRAND CORPUS (site + social) —————  
\"\"\"{corpus}\"\"\"
"""

    stream = client.chat.completions.create(
        model="gpt-4",
        stream=True,
        messages=[
            {"role": "system", "content": "You are concise yet deeply insightful."},
            {"role": "user",   "content": prompt}
        ],
    )

    buffer = ""
    for ch in stream:
        delta = ch.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            buffer += delta.content
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip():
                    yield line.strip() + "\n"
    if buffer.strip():
        yield buffer.strip() + "\n"
