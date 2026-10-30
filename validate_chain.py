"""Read-only validation of the legacy QuantumM38 learning-chain format."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

INITIAL_TARGET = 2**240
GENESIS_PREVIOUS_HASH = "0" * 64
FIELDS = {"block_id", "data", "nonce", "hash", "previous_hash",
          "block_time_seconds", "new_target", "timestamp"}
HEX_HASH = re.compile(r"[0-9a-f]{64}\Z")


def calculate_hash(data, previous_hash, nonce):
    # Preserve the miner's legacy encoding; changing it invalidates old blocks.
    return hashlib.sha256(f"{data}{previous_hash}{nonce}".encode()).hexdigest()


def valid_proof(hash_hex, target):
    return int(hash_hex, 16) < target


def next_targets(target, elapsed):
    # mining.py branches on unrounded time, then stores round(elapsed, 3).
    # At exactly 3.000 the stored value cannot identify the original branch.
    factors = (0.9, 1.1) if elapsed == 3 else ((0.9,) if elapsed < 3 else (1.1,))
    # Deliberately reproduce the legacy float arithmetic, not integer ratios.
    return {int(target * factor) for factor in factors}


def schema_errors(block):
    if not isinstance(block, dict) or set(block) != FIELDS:
        return ["Ungültige oder fehlende Blockfelder"]
    errors = []
    for key in ("block_id", "nonce", "new_target"):
        if type(block[key]) is not int or block[key] < (0 if key == "nonce" else 1):
            errors.append(f"Ungültiges Feld: {key}")
    if type(block["new_target"]) is int and block["new_target"] > 2**256:
        errors.append("new_target außerhalb des Wertebereichs")
    if not isinstance(block["data"], str):
        errors.append("data muss Text sein")
    for key in ("hash", "previous_hash"):
        if not isinstance(block[key], str) or not HEX_HASH.fullmatch(block[key]):
            errors.append(f"Ungültiges Feld: {key}")
    elapsed = block["block_time_seconds"]
    if (type(elapsed) not in (int, float) or elapsed < 0 or
            elapsed > 1e100 or not math.isfinite(elapsed)):
        errors.append("Ungültige block_time_seconds")
    stamp = block["timestamp"]
    try:
        if not isinstance(stamp, str):
            raise ValueError
        datetime.fromisoformat(stamp)
    except ValueError:
        errors.append("Ungültiger timestamp")
    return errors


def validate_chain(blocks):
    """Return errors, never modify blocks. Empty or malformed input fails closed."""
    if not isinstance(blocks, list) or not blocks:
        return ["Keine Blöcke vorhanden"]
    errors = []
    for index, block in enumerate(blocks, 1):
        errors.extend(f"Block {index}: {error}" for error in schema_errors(block))
    if errors:
        return errors
    target = INITIAL_TARGET
    previous_hash = GENESIS_PREVIOUS_HASH
    for index, block in enumerate(blocks, 1):
        prefix = f"Block {index}: "
        if block["block_id"] != index:
            errors.append(prefix + "block_id muss fortlaufend ab 1 sein")
        if block["previous_hash"] != previous_hash:
            errors.append(prefix + "previous_hash stimmt nicht")
        calculated = calculate_hash(block["data"], block["previous_hash"], block["nonce"])
        if calculated != block["hash"]:
            errors.append(prefix + "Hash manipuliert")
        if not valid_proof(calculated, target):
            errors.append(prefix + "Proof-of-Work ungültig (Hash >= Target)")
        if block["new_target"] not in next_targets(target, block["block_time_seconds"]):
            errors.append(prefix + "new_target entspricht nicht der Difficulty-Regel")
            # Never use an unvalidated target to authorize later proofs.
            return errors
        target = block["new_target"]
        previous_hash = block["hash"]
    return errors


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Doppeltes JSON-Feld: {key}")
        result[key] = value
    return result


def load_blocks(directory):
    paths = list(Path(directory).iterdir())
    numbered = []
    for path in paths:
        match = re.fullmatch(r"block_([1-9][0-9]*)\.json", path.name)
        if not match or not path.is_file():
            raise ValueError(f"Unerwarteter Eintrag: {path.name}")
        numbered.append((int(match[1]), path))
    numbered.sort()
    blocks = []
    for expected, (number, path) in enumerate(numbered, 1):
        if number != expected:
            raise ValueError("Blockdateien müssen lückenlos ab block_1.json vorliegen")
        with path.open(encoding="utf-8") as stream:
            blocks.append(json.load(stream, object_pairs_hook=unique_object))
    return blocks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="blocks")
    args = parser.parse_args(argv)
    try:
        errors = validate_chain(load_blocks(args.directory))
    except (OSError, ValueError, RecursionError) as exc:
        errors = [f"Blockdateien nicht lesbar: {exc}"]
    for error in errors:
        print(f"❌ {error}")
    print("⛔ Blockchain ist UNGÜLTIG" if errors else "✅ Blockchain ist gültig")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
