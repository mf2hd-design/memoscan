import time

# Optional: simple domain cleaner if you need one
def clean_url(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url

# ✅ Mocked streaming generator to simulate six memorability key results
def run_memoscan_stream(url):
    yield "Emotional Impact|7|The brand creates some emotional resonance through visuals and messaging."
    time.sleep(1)
    yield "Attention|5|Some elements capture attention, but the story lacks uniqueness."
    time.sleep(1)
    yield "Clarity|8|Clear messaging and strong layout make the story easy to grasp."
    time.sleep(1)
    yield "Involvement|6|The brand invites interaction, but could go further."
    time.sleep(1)
    yield "Repetition|4|Core elements are not used consistently across pages."
    time.sleep(1)
    yield "Consistency|7|The design and tone are mostly aligned, but minor misalignments exist."
