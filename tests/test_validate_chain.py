import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import validate_chain as validator

ROOT = Path(__file__).resolve().parents[1]


def mine_chain(count=2):
    """Independent fixture miner using the repository's actual starting target."""
    blocks, previous, target = [], "0" * 64, 2**240
    for index in range(1, count + 1):
        nonce = 0
        while True:
            digest = hashlib.sha256(f"fixture{previous}{nonce}".encode()).hexdigest()
            if int(digest, 16) < target:
                break
            nonce += 1
        target = int(target * 0.9)
        blocks.append(dict(block_id=index, data="fixture", nonce=nonce, hash=digest,
                           previous_hash=previous, block_time_seconds=0.01,
                           new_target=target, timestamp="2026-10-30T00:00:00"))
        previous = digest
    return blocks


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = mine_chain()

    def setUp(self):
        self.blocks = copy.deepcopy(self.fixture)

    def assert_error(self, text):
        self.assertTrue(any(text in e for e in validator.validate_chain(self.blocks)))

    def test_valid_chain(self):
        self.assertEqual(validator.validate_chain(self.blocks), [])

    def test_valid_genesis_alone(self):
        self.assertEqual(validator.validate_chain(self.blocks[:1]), [])

    def test_data_mutations_every_block(self):
        for index in range(2):
            with self.subTest(index=index):
                self.blocks = copy.deepcopy(self.fixture)
                self.blocks[index]["data"] += "tampered"
                self.assert_error("Hash manipuliert")

    def test_nonce_mutations_every_block(self):
        for index in range(2):
            with self.subTest(index=index):
                self.blocks = copy.deepcopy(self.fixture)
                self.blocks[index]["nonce"] += 1
                self.assert_error("Hash manipuliert")

    def test_genesis_parent(self):
        self.blocks[0]["previous_hash"] = "1" * 64
        self.assert_error("previous_hash")

    def test_broken_link(self):
        self.blocks[1]["previous_hash"] = "0" * 64
        self.assert_error("previous_hash")

    def test_hash_consistent_but_invalid_pow_each_block(self):
        for index in range(2):
            with self.subTest(index=index):
                self.blocks = copy.deepcopy(self.fixture)
                block = self.blocks[index]
                target = 2**240 if index == 0 else self.blocks[0]["new_target"]
                nonce = 0
                while True:
                    digest = hashlib.sha256(f"{block['data']}{block['previous_hash']}{nonce}".encode()).hexdigest()
                    if int(digest, 16) >= target:
                        break
                    nonce += 1
                block.update(nonce=nonce, hash=digest)
                if index == 0:
                    self.blocks = self.blocks[:1]
                errors = validator.validate_chain(self.blocks)
                self.assertTrue(any("Proof-of-Work" in e for e in errors))
                self.assertFalse(any("Hash manipuliert" in e for e in errors))

    def test_target_equality_is_invalid(self):
        self.assertFalse(validator.valid_proof(f"{2**240:064x}", 2**240))
        self.assertTrue(validator.valid_proof(f"{2**240-1:064x}", 2**240))

    def test_genesis_uses_initial_not_new_target(self):
        block = validator.load_blocks(ROOT / "blocks")[0]
        self.assertGreater(int(block["hash"], 16), block["new_target"])
        self.assertEqual(validator.validate_chain([block]), [])

    def test_target_inflation(self):
        self.blocks[0]["new_target"] = 2**256
        self.assert_error("Difficulty-Regel")

    def test_later_block_uses_predecessor_target(self):
        target = self.blocks[0]["new_target"]
        with patch.object(validator, "calculate_hash", side_effect=[self.blocks[0]["hash"], f"{target:064x}"]):
            self.assert_error("Proof-of-Work")

    def test_rounded_time_boundary(self):
        target = 2**240
        self.assertEqual(validator.next_targets(target, 3.0), {int(target * .9), int(target * 1.1)})
        self.assertEqual(validator.next_targets(target, 2.999), {int(target * .9)})
        self.assertEqual(validator.next_targets(target, 3.001), {int(target * 1.1)})

    def test_empty_chain(self):
        self.assertTrue(validator.validate_chain([]))

    def test_missing_genesis_duplicate_or_reordered_ids(self):
        for blocks in (self.blocks[1:], self.blocks[::-1], [self.blocks[0]] * 2):
            with self.subTest(blocks=blocks):
                self.assertTrue(validator.validate_chain(blocks))

    def test_malformed_fields(self):
        for field, value in (("nonce", True), ("nonce", -1), ("data", 1),
                             ("hash", "g" * 64), ("previous_hash", "00"),
                             ("block_id", True), ("new_target", 0),
                             ("new_target", 2**256+1), ("timestamp", None),
                             ("block_time_seconds", float("nan")),
                             ("block_time_seconds", float("inf")),
                             ("block_time_seconds", -1), ("block_time_seconds", True)):
            with self.subTest(field=field, value=value):
                self.blocks = copy.deepcopy(self.fixture)
                self.blocks[0][field] = value
                self.assertTrue(validator.validate_chain(self.blocks))

    def test_missing_and_unknown_fields(self):
        del self.blocks[0]["nonce"]
        self.assert_error("Blockfelder")
        self.blocks = copy.deepcopy(self.fixture)
        self.blocks[0]["target"] = 2**256
        self.assert_error("Blockfelder")

    def test_non_object_block(self):
        self.assertTrue(validator.validate_chain([None]))

    def test_does_not_modify_input(self):
        before = copy.deepcopy(self.blocks)
        validator.validate_chain(self.blocks)
        self.assertEqual(self.blocks, before)

    def test_original_blocks_detect_existing_corruption(self):
        errors = validator.validate_chain(validator.load_blocks(ROOT / "blocks"))
        self.assertIn("Block 3: Hash manipuliert", errors)
        self.assertIn("Block 4: previous_hash stimmt nicht", errors)

    def test_numeric_file_order(self):
        with tempfile.TemporaryDirectory() as directory:
            for index in range(1, 12):
                Path(directory, f"block_{index}.json").write_text(json.dumps({"block_id": index}))
            self.assertEqual([b["block_id"] for b in validator.load_blocks(directory)], list(range(1, 12)))

    def test_bad_files_fail_closed(self):
        for filename, content in (("block_2.json", "{}"), ("other.json", "{}"),
                                  ("block_1.json", "{"),
                                  ("block_1.json", '{"nonce": 1, "nonce": 2}')):
            with self.subTest(filename=filename, content=content), tempfile.TemporaryDirectory() as directory:
                Path(directory, filename).write_text(content)
                with self.assertRaises(ValueError):
                    validator.load_blocks(directory)

    def test_cli_exit_codes_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "block_1.json")
            for block, expected in ((self.blocks[0], 0), ({**self.blocks[0], "data": "tampered"}, 1)):
                path.write_text(json.dumps(block))
                before = path.read_bytes()
                result = subprocess.run([sys.executable, str(ROOT / "validate_chain.py"), directory], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(path.read_bytes(), before)

    def test_cli_empty_and_missing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in (directory, str(Path(directory, "missing"))):
                result = subprocess.run([sys.executable, str(ROOT / "validate_chain.py"), name], capture_output=True)
                self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
