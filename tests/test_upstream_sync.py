import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "sync" / "upstream-sync"


def call(*args):
    return subprocess.run([str(BOT), *map(str, args)], text=True, capture_output=True)


class UpstreamSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.repo = self.path / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "bot@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "test bot"], cwd=self.repo, check=True)
        (self.repo / "base.txt").write_text("base\n")
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=self.repo, check=True)
        self.revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()
        self.archive = self.path / "component.tar.xz"
        self.archive.write_bytes(b"fixture archive")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, *, sha=None, status="locked"):
        sha = sha or hashlib.sha256(self.archive.read_bytes()).hexdigest()
        record = self.path / "component.yaml"
        record.write_text(f'''name: component
status: {status}
upstream: https://example.invalid/component
source_type: git
revision: {self.revision}
archive: component.tar.xz
sha256: {sha}
license: MIT
retrieved_at: 2026-09-02T00:00:00Z
provenance:
  archive_url: https://example.invalid/component.tar.xz
  retrieved_by: test-bot
  retrieval_method: automation
  evidence:
    - release-1
''')
        return record

    def test_accepts_verified_local_candidate(self):
        report = self.path / "report.json"
        result = call("--record", self.record(), "--archive", self.archive, "--upstream-repo", self.repo, "--report", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"result": "needs-review"', report.read_text())

    def test_rejects_bad_digest(self):
        result = call("--record", self.record(sha="0" * 64), "--archive", self.archive, "--upstream-repo", self.repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("SHA-256 mismatch", result.stderr)

    def test_rejects_pending_record(self):
        result = call("--record", self.record(status="pending-verification"), "--archive", self.archive, "--upstream-repo", self.repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("status: locked", result.stderr)

    def test_applies_patch_in_disposable_worktree(self):
        patch_dir = self.path / "patches"
        patch_dir.mkdir()
        (self.repo / "base.txt").write_text("patched\n")
        subprocess.run(["git", "commit", "-am", "patch fixture", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "format-patch", "-1", "--output-directory", str(patch_dir)], cwd=self.repo, check=True)
        subprocess.run(["git", "reset", "--hard", self.revision, "-q"], cwd=self.repo, check=True)
        result = call("--record", self.record(), "--archive", self.archive, "--upstream-repo", self.repo, "--patch-dir", patch_dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"patches_tested": 1', result.stdout)
