"""Directly call retrieve_chunks (bypass API) to get chunk_id for each query."""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from apps.immoweb.hal_knowledge import retrieve_chunks

QUERIES = [
    ("G-BIS PRIMARY", "Quanto costa un render Virtual Staging?"),
    ("G-BIS ALT", "Quanto spendo in crediti per lo staging?"),
    ("CAP10 cos-e", "Cos'è HAL Agent in OMNIA?"),
    ("CAP10 improve", "A cosa serve il pulsante Migliora con HAL nei form?"),
    ("CAP10 limiti", "Cosa NON può fare HAL Agent?"),
]

async def main():
    for label, q in QUERIES:
        print(f"\n===== {label}: {q}")
        chunks = await retrieve_chunks(q, k=5)
        for i, c in enumerate(chunks, 1):
            print(f"  #{i} file={c.get('file')} chunk_id={c.get('chunk_id')} section={c.get('section')} sim={c.get('similarity')}")

if __name__ == "__main__":
    asyncio.run(main())
