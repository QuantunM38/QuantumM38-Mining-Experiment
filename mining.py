import hashlib
import json
import time
from datetime import datetime
import os

DATA = "QuantumM38"
BLOCK_COUNT = 5
TARGET_BLOCK_TIME = 3

target = 2**240
previous_hash = "0" * 64

os.makedirs("blocks", exist_ok=True)

for block_id in range(1, BLOCK_COUNT + 1):
    nonce = 0
    start_time = time.time()

    while True:
        text = f"{DATA}{previous_hash}{nonce}"
        hash_hex = hashlib.sha256(text.encode()).hexdigest()
        hash_int = int(hash_hex, 16)

        if hash_int < target:
            elapsed = time.time() - start_time

            # Difficulty anpassen
            if elapsed < TARGET_BLOCK_TIME:
                target = int(target * 0.9)
            else:
                target = int(target * 1.1)

            block = {
                "block_id": block_id,
                "data": DATA,
                "nonce": nonce,
                "hash": hash_hex,
                "previous_hash": previous_hash,
                "block_time_seconds": round(elapsed, 3),
                "new_target": target,
                "timestamp": datetime.utcnow().isoformat()
            }

            with open(f"blocks/block_{block_id}.json", "w") as f:
                json.dump(block, f, indent=2)

            print(f"Block {block_id} gefunden in {round(elapsed,3)}s")

            previous_hash = hash_hex
            break

        nonce += 1