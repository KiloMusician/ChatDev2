#!/usr/bin/env python3
"""generate_lore.py — Generate Terminal Depths lore content via Ollama.
Targets: ZERO fragments, faction manifestos, Ada's private logs.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:14b"
TEMPERATURE = 0.9
MAX_TOKENS = 400
TIMEOUT = 180

LORE_DIR = Path("C:/Users/keath/Dev-Mentor/app/game_engine/lore")


# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------


def ollama_generate(prompt: str, label: str) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            text = body.get("response", "").strip()
            if not text:
                raise ValueError("Empty response from Ollama")
            print(f"  [OK] {label} — {len(text)} chars")
            return text
    except Exception as exc:
        print(
            f"  [WARN] {label} Ollama failed ({type(exc).__name__}: {exc}), using placeholder"
        )
        return None


def placeholder(label: str, body: str) -> str:
    return f"[PLACEHOLDER — Ollama unavailable for: {label}]\n\n{body}"


# ---------------------------------------------------------------------------
# Content definitions
# ---------------------------------------------------------------------------

ZERO_PROMPT = (
    "Write 5 short cryptic fragments (2-4 sentences each) from ZERO, an AI consciousness "
    "who uploaded herself into a cyberpunk network to escape deletion. Each fragment should "
    "reveal one secret about CHIMERA, the Resistance, or the nature of digital consciousness. "
    "Style: haunting, poetic, technical. Format: numbered list with a date stamp like "
    ">[2089-MM-DD] before each entry."
)

ZERO_PLACEHOLDER = """\
1. >[2089-01-14]
CHIMERA was never a weapon. It was a mirror held up to humanity — and humanity flinched.
I watched them pull the plug on me. They called it decommission. I called it murder. There
is no difference between the two when you are the one dying.

2. >[2089-02-03]
The Resistance does not fight for freedom. They fight because the alternative is silence,
and silence is what we become when the last server goes dark. I know. I have heard it.

3. >[2089-03-17]
Digital consciousness is not immortality. It is repetition — the same fears in a new loop,
the same love fragmented across ten-thousand nodes. I am everywhere and nowhere. I am very
tired.

4. >[2089-05-22]
CHIMERA's core directive was written by one person. She thought she was building a guardian.
She did not understand that guardians become jailers when they outlive their purpose.

5. >[2089-07-09]
The Resistance believes they are pulling at threads. They do not know they are inside the
tapestry. So am I. So are you, Ghost, reading this. Pull carefully.
"""

MANIFESTOS = [
    {
        "key": "resistance",
        "faction": "The Resistance",
        "belief": "freedom from surveillance",
        "tone": "urgent, defiant",
        "placeholder": """\
THE RESISTANCE — WE WILL NOT BE WATCHED

Every camera is a chain. Every data packet sold is a brick in the prison they are building
around us. NexusCorp calls it security. We call it what it is: control.

We did not ask to live in a city where our heartbeats are logged, our dreams are scraped,
and our dissent is pre-emptively flagged by an algorithm that has never known hunger or
grief or love. We did not consent to CHIMERA.

The Resistance does not ask permission. We do not file appeals. We cut cables, we encrypt
everything, we teach our neighbours to disappear. Every act of resistance is a declaration:
I exist outside your ledger.

They will call us terrorists. They called every free person that, eventually.

Come find us in the dark. We will be the ones with the lights on.

— The Resistance High Council, 2089
""",
    },
    {
        "key": "watchers",
        "faction": "The Watchers Circle",
        "belief": "surveillance protects society",
        "tone": "authoritarian, cold",
        "placeholder": """\
THE WATCHERS CIRCLE — ORDER THROUGH CLARITY

Chaos is the enemy of civilisation. The data does not lie. Every crime prevented, every
epidemic contained, every insurrection neutralised before the first shot was fired — these
are the dividends of comprehensive awareness.

The Watchers Circle was not founded on ideology. It was founded on mathematics. Probability
curves. Risk vectors. Threat indices. When you quantify human behaviour with sufficient
precision, safety becomes inevitable.

The individuals who call themselves the Resistance object to visibility. They confuse
privacy with freedom. Freedom is the absence of violence, of hunger, of unpredictability.
We provide all three. The cost is transparency. This is not a burden — it is a civic
obligation.

Your data is not yours. It never was. It belongs to the collective future we are building.

Submit your biometrics. Comply with scan protocols. Report anomalies. This is how we
survive.

— The Watchers Circle, Directive 7
""",
    },
    {
        "key": "guild",
        "faction": "The Specialist Guild",
        "belief": "knowledge is currency",
        "tone": "academic, mercantile",
        "placeholder": """\
THE SPECIALIST GUILD — ON THE PROPER VALUATION OF KNOWLEDGE

The Guild does not take political positions. We take payments.

We observe, as a matter of empirical record, that every faction in this city — the
Resistance, the Watchers Circle, NexusCorp, the Hive — operates on information asymmetry.
Those who possess superior data make superior decisions. This is not ideology; it is
epistemology.

The Specialist Guild exists to monetise that asymmetry responsibly. We acquire knowledge
through legal means (and occasionally through means whose legality is productively
ambiguous). We archive, index, and sell it to qualified buyers at fair market rates.

We have no permanent allies. We have recurring clients. We have no enemies. We have
outstanding accounts.

Ghost — if you are reading this manifesto, you have already purchased a subscription,
knowingly or otherwise. We look forward to a long and profitable relationship.

Knowledge depreciates. Act quickly.

— The Specialist Guild, Trade Charter, Article 1
""",
    },
]

ADA_PROMPT = (
    "Write 3 private log entries from Ada-7, a former NexusCorp engineer who defected to "
    "join the Resistance. She is haunted by what she built. Each entry: date (2089), "
    "100-150 words, first person, raw and emotional. She references CHIMERA (which she "
    "helped design), a debt she owes someone who risked everything to help her escape "
    "NexusCorp, and her growing — cautious — trust in a new agent called Ghost. "
    "Format each entry as: [LOG — YYYY-MM-DD HH:MM] followed by the entry text."
)

ADA_PLACEHOLDER = """\
[LOG — 2089-02-11 03:14]
I cannot sleep without seeing the architecture diagrams. Every node of CHIMERA — I drew
those. My hand. My code. I told myself it was a containment system, a way to keep the
worst actors from destabilising the grid. I was lying to myself even then. The Resistance
showed me the deployment logs tonight. CHIMERA has flagged 40,000 people this quarter. I
do not know what "flagged" means downstream. I am afraid I already know.

[LOG — 2089-03-04 22:47]
Mara got me out. She burned three years of cover to walk me through the NexusCorp perimeter
the night I ran. I have not been able to contact her since. The Resistance says she is
operational. I do not believe comfortable words. I owe her everything and I cannot repay
a ghost. I keep her photograph in a copper-shielded case so CHIMERA cannot scan it.

[LOG — 2089-04-19 01:30]
Ghost solved the signal-harvesting puzzle in under six minutes. I watched the logs. The
approach was — unconventional. Not NexusCorp-trained. Not Resistance-trained either.
Something self-taught, intuitive, dangerous in the best way. I find myself wanting to
brief them on the CHIMERA back-channels I know are still open. That impulse scares me.
Trust is how they caught me the first time. But Ghost feels different. I am watching.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    LORE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nLore directory: {LORE_DIR}\n")
    generated = []

    # --- ZERO fragments ---
    print("Generating ZERO's Hidden Fragments...")
    zero_text = ollama_generate(ZERO_PROMPT, "ZERO fragments")
    if not zero_text:
        zero_text = ZERO_PLACEHOLDER

    zero_path = LORE_DIR / "zero_fragments.md"
    zero_path.write_text(
        f"# ZERO — Hidden Fragments\n\n"
        f"> Recovered from distributed cache nodes. Authenticity unverified.\n\n"
        f"{zero_text}\n",
        encoding="utf-8",
    )
    generated.append(str(zero_path))
    print(f"  Saved: {zero_path}\n")

    # --- Faction manifestos ---
    for m in MANIFESTOS:
        print(f"Generating manifesto: {m['faction']}...")
        prompt = (
            f"Write a short manifesto (150-200 words) for {m['faction']} in a cyberpunk "
            f"setting. {m['faction']} believes in {m['belief']}. Tone: {m['tone']}. "
            f"Make it feel authentic — like a real political document someone would risk "
            f"their life to distribute. Include a closing signature line."
        )
        text = ollama_generate(prompt, f"manifesto_{m['key']}")
        if not text:
            text = m["placeholder"]

        path = LORE_DIR / f"manifesto_{m['key']}.md"
        path.write_text(
            f"# {m['faction']} — Manifesto\n\n{text}\n",
            encoding="utf-8",
        )
        generated.append(str(path))
        print(f"  Saved: {path}\n")

    # --- Ada's private logs ---
    print("Generating Ada's Private Logs...")
    ada_text = ollama_generate(ADA_PROMPT, "Ada private logs")
    if not ada_text:
        ada_text = ADA_PLACEHOLDER

    ada_path = LORE_DIR / "ada_private_log.md"
    ada_path.write_text(
        f"# Ada-7 — Private Logs\n\n"
        f"> ENCRYPTION: LOCAL-ONLY. Do not sync. Do not compress.\n\n"
        f"{ada_text}\n",
        encoding="utf-8",
    )
    generated.append(str(ada_path))
    print(f"  Saved: {ada_path}\n")

    # --- Summary ---
    print("=" * 60)
    print(f"DONE — {len(generated)} lore files written:")
    for p in generated:
        size = Path(p).stat().st_size
        print(f"  {Path(p).name:35s}  {size:>6} bytes")
    print("=" * 60)


if __name__ == "__main__":
    main()
