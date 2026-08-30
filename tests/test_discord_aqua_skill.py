import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / ".codex/skills/discord-aqua-repair/SKILL.md"
OBSERVER = ROOT / ".codex/skills/discord-aqua-repair/scripts/observe_latency.py"


class AquaSkillTests(unittest.TestCase):
    def test_skill_contains_safety_contract(self):
        text = SKILL.read_text()
        for phrase in ("one `set_recording`", "Codex Computer Use only", "Desired FPS", "Effective FPS", "CAPTCHA", "p50", "p95", "p99"):
            self.assertIn(phrase, text)
        self.assertNotIn("/Users/", text)

    def test_observer_percentiles_and_read_only_result(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "events.jsonl", Path(d) / "result.json"
            rows = [{"phase": "before", "recording_state": False}]
            rows += [{"phase": p, "t_ms": t} for p, t in [("start", 1), ("start", 2), ("start", 3), ("stop", 4), ("stop", 5), ("stop", 6)]]
            rows += [{"phase": "after", "recording_state": False}]
            src.write_text("\n".join(json.dumps(row) for row in rows))
            subprocess.run([sys.executable, str(OBSERVER), "--input", str(src), "--output", str(dst)], check=True)
            result = json.loads(dst.read_text())
            self.assertTrue(result["read_only"])
            self.assertEqual(result["restoration"], "verified")
            self.assertEqual(result["samples"]["start"]["count"], 3)
            self.assertEqual(result["samples"]["stop"]["p95"], 5.9)

    def test_observer_fails_closed_without_explicit_restoration(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "events.jsonl", Path(d) / "result.json"
            src.write_text(json.dumps({"phase": "before", "recording_state": False}))
            subprocess.run([sys.executable, str(OBSERVER), "--input", str(src), "--output", str(dst)], check=True)
            self.assertEqual(json.loads(dst.read_text())["restoration"], "inconclusive")

    def test_observer_fails_closed_on_malformed_input(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "events.jsonl", Path(d) / "result.json"
            src.write_text("not-json\n")
            subprocess.run([sys.executable, str(OBSERVER), "--input", str(src), "--output", str(dst)], check=True)
            self.assertEqual(json.loads(dst.read_text())["restoration"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
