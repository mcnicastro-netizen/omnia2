"""
OMNIA — Sora 2 video concept generator
4 cinematic scene pilot per founder demo concept.
"""
import os
import sys
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

sys.path.insert(0, '/app/backend')
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

OUT_DIR = '/app/demo_videos'
os.makedirs(OUT_DIR, exist_ok=True)

SCENES = [
    {
        "id": 1,
        "name": "future_skyline_omnia",
        "prompt": (
            "Cinematic aerial drone shot at golden hour over a modern Italian city skyline "
            "(Milan-inspired). Subtle holographic data overlays float gently around the buildings — "
            "elegant golden price tags, AI property markers, glowing data streams connecting rooftops. "
            "The Duomo cathedral is reimagined with subtle futuristic LED accents. "
            "Premium color palette: warm gold + deep cyan tech accents + soft white particles. "
            "Slow forward camera motion. Ultra-luxury, future-forward, like a Bladerunner 2049 "
            "real estate vision but warmer. 4K cinema quality. No text. No people. Pure atmosphere."
        ),
    },
    {
        "id": 2,
        "name": "holographic_property_map",
        "prompt": (
            "Futuristic holographic 3D map of an Italian urban district floating in dark space, "
            "ultra-modern UI like Iron Man Jarvis but more elegant and minimal. Golden glowing property "
            "pins rise from the map with animated data labels (€450K, AI Score 92, Class A). "
            "A digital camera smoothly zooms into one specific property which expands into a 3D building model. "
            "Sleek cyan grid background, particles flowing. Premium AI-powered real estate visualization. "
            "Color palette: gold + deep navy + cyan accents. No text on screen. Smooth cinematic motion. "
            "Conveys 'AI ecosystem managing real estate intelligence'. 4K cinema."
        ),
    },
    {
        "id": 3,
        "name": "agent_ai_assistant",
        "prompt": (
            "Cinematic close-up shot of a sophisticated 40-year-old Italian woman real estate agent "
            "in a modern minimalist luxury office, looking at her smartphone with quiet confidence. "
            "Above the phone, elegant holographic AI notifications float in golden light: "
            "'AI Lead Score 92', 'Perfect Match Found', 'Smart Contract Ready'. "
            "Soft warm cinematic lighting, shallow depth of field, premium ambiance. "
            "Her face shows assured intelligence — she trusts the AI. "
            "Background: floor-to-ceiling windows with city skyline blurred. "
            "Premium business future-tech aesthetic. No text in subtitles. 4K cinema, slow push-in motion."
        ),
    },
    {
        "id": 4,
        "name": "family_smart_keys_future",
        "prompt": (
            "Cinematic shot of a young Italian family (parents in their 30s + 2 happy children, "
            "boy 8 and girl 5) receiving keys to their new modern home. The key is a sleek glass-and-gold "
            "smart key with a subtle blue glow inside. Behind them, the modern luxury apartment "
            "interior shows subtle augmented reality holographic overlays highlighting room features — "
            "smart heating, security, integrated AI assistant. Golden hour light streams through "
            "floor-to-ceiling windows. The family is joyful but the scene is premium and modern. "
            "Future of property ownership. Color palette: warm gold + soft white + cyan tech accents. "
            "4K cinema. Emotional yet futuristic. No text. Slow dolly-in."
        ),
    },
]


def generate_scene(scene):
    """Generate a single Sora 2 scene"""
    out_path = os.path.join(OUT_DIR, f"scene_{scene['id']}_{scene['name']}.mp4")
    print(f"[scene {scene['id']}] starting...", flush=True)
    t0 = time.time()
    try:
        video_gen = OpenAIVideoGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])
        video_bytes = video_gen.text_to_video(
            prompt=scene['prompt'],
            model="sora-2",
            size="1280x720",
            duration=8,
            max_wait_time=900,
        )
        if video_bytes:
            video_gen.save_video(video_bytes, out_path)
            elapsed = int(time.time() - t0)
            size_mb = round(os.path.getsize(out_path) / 1024 / 1024, 2)
            print(f"[scene {scene['id']}] DONE in {elapsed}s, {size_mb}MB -> {out_path}", flush=True)
            return {"id": scene['id'], "name": scene['name'], "status": "ok", "path": out_path, "elapsed": elapsed, "size_mb": size_mb}
        else:
            print(f"[scene {scene['id']}] FAILED (no bytes)", flush=True)
            return {"id": scene['id'], "name": scene['name'], "status": "fail", "error": "no_bytes"}
    except Exception as e:
        print(f"[scene {scene['id']}] ERROR: {e}", flush=True)
        traceback.print_exc()
        return {"id": scene['id'], "name": scene['name'], "status": "error", "error": str(e)}


def main():
    print("=" * 60)
    print("OMNIA SORA 2 CONCEPT GENERATION - 4 SCENES PILOT")
    print("=" * 60)
    print(f"Output dir: {OUT_DIR}")
    print(f"Model: sora-2, size: 1280x720 HD landscape, duration: 8s")
    print(f"Started at: {time.strftime('%H:%M:%S')}")
    print("=" * 60)

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(generate_scene, s): s for s in SCENES}
        for fut in as_completed(futures):
            results.append(fut.result())

    # Write status file
    status_file = os.path.join(OUT_DIR, "status.json")
    with open(status_file, 'w') as f:
        json.dump({"completed_at": time.strftime('%Y-%m-%d %H:%M:%S'), "results": results}, f, indent=2)

    print("\n" + "=" * 60)
    print("FINAL STATUS")
    print("=" * 60)
    ok = sum(1 for r in results if r['status'] == 'ok')
    print(f"OK: {ok}/4")
    for r in results:
        print(f"  scene {r['id']} ({r['name']}): {r['status']}")
    print(f"\nStatus saved to: {status_file}")


if __name__ == "__main__":
    main()
