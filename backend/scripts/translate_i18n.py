"""One-shot: translate missing i18n keys IT → EN/ES via Gemini. Run from /app/backend."""
import asyncio
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

LOCALES = "/app/frontend/src/shared/i18n/locales"
BATCH = 50


def flat(d, p=""):
    out = {}
    for k, v in d.items():
        key = f"{p}.{k}" if p else k
        if isinstance(v, dict):
            out.update(flat(v, key))
        else:
            out[key] = v
    return out


def unflat_set(d, dotted, value):
    parts = dotted.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


async def translate_batch(items, lang_name):
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=f"i18n-{lang_name}-{hash(tuple(items))}",
        system_message=(
            f"You are a professional translator for an Italian real-estate SaaS platform (OMNIA). "
            f"Translate the JSON values from Italian to {lang_name}. Keep the exact same JSON keys. "
            f"Preserve any placeholders like {{{{name}}}} exactly. Keep real-estate terminology natural "
            f"({lang_name} market conventions). Respond ONLY with valid JSON, no markdown fences."
        ),
    ).with_model("gemini", "gemini-3-flash-preview")
    payload = json.dumps(dict(items), ensure_ascii=False)
    raw = await chat.send_message(UserMessage(text=payload))
    txt = str(raw).strip()
    if txt.startswith("```"):
        txt = txt.split("```")[1]
        if txt.startswith("json"):
            txt = txt[4:]
    return json.loads(txt)


async def main():
    it = json.load(open(f"{LOCALES}/it.json"))
    it_flat = flat(it)
    for lang_code, lang_name in [("en", "English"), ("es", "Spanish")]:
        target = json.load(open(f"{LOCALES}/{lang_code}.json"))
        target_flat = flat(target)
        missing = [(k, v) for k, v in it_flat.items() if k not in target_flat and isinstance(v, str)]
        print(f"[{lang_code}] missing: {len(missing)}")
        translated = {}
        batches = [missing[i:i + BATCH] for i in range(0, len(missing), BATCH)]
        for bi in range(0, len(batches), 4):
            group = batches[bi:bi + 4]
            results = await asyncio.gather(*[translate_batch(b, lang_name) for b in group], return_exceptions=True)
            for b, res in zip(group, results):
                if isinstance(res, Exception):
                    print(f"[{lang_code}] batch failed: {res}", file=sys.stderr)
                    continue
                translated.update(res)
            print(f"[{lang_code}] progress: {len(translated)}/{len(missing)}")
        for k, v in translated.items():
            if k in it_flat:
                unflat_set(target, k, v)
        json.dump(target, open(f"{LOCALES}/{lang_code}.json", "w"), ensure_ascii=False, indent=2)
        print(f"[{lang_code}] written. total keys now: {len(flat(target))}")


asyncio.run(main())
