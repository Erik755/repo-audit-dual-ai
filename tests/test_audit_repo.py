import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_repo.py"
SPEC = importlib.util.spec_from_file_location("audit_repo", SCRIPT)
audit_repo = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(audit_repo)


class RepositoryAuditTests(unittest.TestCase):
    def make_repository(self, parent: Path) -> tuple[Path, str]:
        repo = parent / "sample"
        (repo / "src").mkdir(parents=True)
        (repo / "tests").mkdir()
        (repo / ".github" / "workflows").mkdir(parents=True)
        secret_marker = "PRIVATE-SOURCE-CONTENT-DO-NOT-LEAK"
        (repo / "README.md").write_text("# Sample\n", encoding="utf-8")
        (repo / "LICENSE").write_text("test fixture\n", encoding="utf-8")
        (repo / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
        (repo / ".gitignore").write_text(".venv/\n", encoding="utf-8")
        (repo / "src" / "app.py").write_text(f"VALUE = {secret_marker!r}\n", encoding="utf-8")
        (repo / "tests" / "test_app.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        (repo / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
        return repo, secret_marker

    def test_deterministic_report_is_complete_and_does_not_leak_source(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            repo, marker = self.make_repository(Path(temp))
            report = audit_repo.build_report(repo)
            serialized = json.dumps(report)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["ai_review"]["status"], "not_requested")
        self.assertGreater(report["scores"]["total"], 0)
        self.assertEqual(report["inventory"]["test_source_files"], 1)
        self.assertNotIn(marker, serialized)
        self.assertNotIn(str(repo), serialized)

    def test_ai_payload_contains_only_aggregate_sections(self):
        report = {
            "inventory": {"source_files": 1}, "signals": {"ci": False},
            "history": {"commit_count": 1}, "scores": {"total": 40},
            "limitations": ["tests not run"], "repository": {"name": "private-name"},
        }
        payload = audit_repo._safe_ai_payload(report)
        self.assertEqual(set(payload), {"inventory", "signals", "history", "scores", "limitations"})
        self.assertNotIn("private-name", json.dumps(payload))

    def test_provider_json_extraction(self):
        value = audit_repo._extract_json('```json\n{"executive_summary":"ok","priorities":[]}\n```')
        self.assertEqual(value["executive_summary"], "ok")


if __name__ == "__main__":
    unittest.main()

