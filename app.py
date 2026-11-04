"""Brand Face-Off: competitor analysis agent (demo data + optional Claude insights).
Run:  uvicorn app:app --reload   then open http://127.0.0.1:8000
"""
import hashlib, os, random
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Brand Face-Off")
app.mount("/static", StaticFiles(directory="static"), name="static")

CATS = ["Search visibility", "Reputation", "Paid activity", "Keyword strategy",
        "Social presence", "Website quality", "Local presence"]
DEFAULT_W = [25, 20, 15, 15, 10, 10, 5]  # weights from the PRD


class Req(BaseModel):
    a: str
    b: str
    industry: str = "General"
    location: str = "Chennai, India"
    weights: list[float] = DEFAULT_W


def rng(*parts):
    seed = int(hashlib.sha256("|".join(parts).lower().encode()).hexdigest(), 16)
    return random.Random(seed)


def collect(name, industry):
    """DEMO collector. Replace with Google Places / Meta Ad Library / SERP APIs."""
    r = rng(name, industry)
    c = [round(35 + r.random() * 60) for _ in CATS]
    m = {
        "Google rating": f"{3 + c[1] / 100 * 1.9:.1f} ★",
        "Reviews": round(300 + c[1] * 95),
        "Reviews / month": round(c[1] * 0.9 + r.random() * 20),
        "Active Meta ads": round(c[2] * 0.9),
        "Keywords tracked": round(100 + c[3] * 28),
        "Top-10 keywords": round(c[0] * 0.6),
        "Followers (k)": round(2 + c[4] * 1.6),
        "Page speed": c[5],
        "GBP completeness %": c[6],
    }
    return {"name": name, "cats": c, "metrics": m,
            "source": "demo-data", "timestamp": "simulated"}


def score(x, w):
    return round(sum(s * wt for s, wt in zip(x["cats"], w)) / (sum(w) or 1), 1)


def insights(a, b, sa, sb, th, ov):
    out = []
    lead, lag = (a, b) if sa >= sb else (b, a)
    out.append(f"Overall: {lead['name']} leads {max(sa, sb)} vs {min(sa, sb)} (gap {round(sa - sb, 1)}).")
    d = sorted(((a["cats"][i] - b["cats"][i], i) for i in range(7)), reverse=True)
    if d[0][0] > 0:
        out.append(f"{a['name']} wins on {CATS[d[0][1]]}: {a['cats'][d[0][1]]} vs {b['cats'][d[0][1]]}.")
    if d[-1][0] < 0:
        i = d[-1][1]
        out.append(f"Biggest weakness for {a['name']}: {CATS[i]} ({a['cats'][i]} vs {b['cats'][i]}).")
    out.append(f"Threat level {th}: keyword overlap {ov}%, score difference {round(sb - sa, 1)}.")
    tips = {0: "Publish pages for the keyword gaps to climb the SERP.",
            1: "Ask happy customers for reviews to lift review velocity.",
            2: "Test more Meta ad creatives.", 3: "Expand keyword coverage by intent cluster.",
            4: "Post more consistently to grow followers.", 5: "Improve page speed and mobile UX.",
            6: "Complete the Google Business Profile."}
    for n, (v, i) in enumerate([x for x in d if x[0] < 0][-3:][::-1], 1):
        out.append(f"Recommendation {n}: {tips[i]} ({CATS[i]}: {a['cats'][i]} vs {b['cats'][i]})")
    return out


def llm_summary(payload):
    """Optional: Claude writes a grounded summary if ANTHROPIC_API_KEY is set."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        msg = anthropic.Anthropic().messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=500,
            system="You are a competitor analyst. Use ONLY the numbers given. Cite metric values. 4 sentences max.",
            messages=[{"role": "user", "content": str(payload)}])
        return msg.content[0].text
    except Exception as e:  # graceful degradation
        return None


@app.post("/api/analyze")
def analyze(r: Req):
    a, b = collect(r.a, r.industry), collect(r.b, r.industry)
    w = r.weights if len(r.weights) == 7 else DEFAULT_W
    sa, sb = score(a, w), score(b, w)
    ov = round(30 + rng(r.a, r.b).random() * 40)
    d = sb - sa
    t = 2 if d > 5 else 1 if d > -8 else 0
    if ov > 55 and t < 2:
        t += 1
    th = ["Low", "Medium", "High"][t]
    k = r.industry.split()[0].lower()
    ins = insights(a, b, sa, sb, th, ov)
    ai = llm_summary({"A": a, "B": b, "scores": [sa, sb], "threat": th})
    return {"cats": CATS, "weights": w, "a": a, "b": b, "sa": sa, "sb": sb,
            "gap": round(sa - sb, 1), "threat": th, "overlap": ov,
            "gaps": [f"best {k} near me", f"{k} deals", f"top {k} brands", f"affordable {k}"],
            "insights": ins, "ai_summary": ai}


@app.get("/")
def home():
    return FileResponse("static/index.html")
