import json
import hashlib
import os

def calculate_hash(data, previous_hash, nonce):
    text = f"{data}{previous_hash}{nonce}"
    return hashlib.sha256(text.encode()).hexdigest()

# Alle Block-Dateien laden
block_files = sorted(os.listdir("blocks"))
blocks = []

for file in block_files:
    with open(f"blocks/{file}", "r") as f:
        blocks.append(json.load(f))

valid = True

for i in range(len(blocks)):
    block = blocks[i]

    # Genesis-Block überspringen (block_1)
    if i == 0:
        continue

    previous_block = blocks[i - 1]

    # 1️⃣ Prüfen: previous_hash stimmt?
    if block["previous_hash"] != previous_block["hash"]:
        print(f"❌ Block {block['block_id']}: previous_hash stimmt nicht")
        valid = False

    # 2️⃣ Prüfen: Hash korrekt berechnet?
    recalculated_hash = calculate_hash(
        block["data"],
        block["previous_hash"],
        block["nonce"]
    )

    if recalculated_hash != block["hash"]:
        print(f"❌ Block {block['block_id']}: Hash manipuliert")
        valid = False

if valid:
    print("✅ Blockchain ist gültig")
else:
    print("⛔ Blockchain ist UNGÜLTIG")