import hashlib
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOT = ROOT / "sync" / "upstream-sync"
CROSS = ROOT / "cross" / "verify-toolchain"


def call(*args):
    return subprocess.run([str(BOT), *map(str, args)], text=True, capture_output=True)


def cross_call(*args, env=None):
    return subprocess.run([str(CROSS), *map(str, args)], text=True, capture_output=True, env=env)


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


class MipsToolchainTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.upstream = self.path / "upstream"
        (self.upstream / "sources").mkdir(parents=True)
        self.cache = self.path / "cache"
        self.cache.mkdir()
        staging = self.path / "staging" / "mips-toolchain"
        (staging / "bin").mkdir(parents=True)
        self.sysroot = staging / "sysroot"
        self.sysroot.mkdir()
        compiler = staging / "bin" / "mipsel-router-linux-musl-gcc"
        compiler.write_text(
            "#!/bin/sh\nroot=$(CDPATH= cd -- \"$(dirname -- \"$0\")/..\" && pwd)\ncase \"$1\" in\n-dumpmachine) echo mipsel-router-linux-musl ;;\n--print-sysroot) echo \"$root/sysroot\" ;;\nesac\n"
        )
        compiler.chmod(0o755)
        self.archive = self.cache / "mips-toolchain.tar.xz"
        with tarfile.open(self.archive, "w:xz") as bundle:
            bundle.add(staging, arcname="mips-toolchain")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.write_source_lock("mips-toolchain", self.archive, digest)
        kernel = self.cache / "linux.tar.xz"
        kernel.write_bytes(b"locked kernel source")
        kernel_digest = hashlib.sha256(kernel.read_bytes()).hexdigest()
        self.write_source_lock("linux", kernel, kernel_digest)

    def tearDown(self):
        self.temp.cleanup()

    def write_source_lock(self, name, archive, digest):
        (self.upstream / "sources" / f"{name}.yaml").write_text(f'''name: {name}
status: locked
upstream: https://example.invalid/{name}
source_type: archive
revision: fixture-1
archive: {archive.name}
sha256: {digest}
license: MIT
retrieved_at: 2026-09-02T00:00:00Z
provenance:
  archive_url: https://example.invalid/{archive.name}
  retrieved_by: test-bot
  retrieval_method: automation
  evidence:
    - fixture-1
''')

    def record(self, status="locked"):
        path = self.path / "mipsel-24kc-musl.yaml"
        path.write_text(f'''name: mipsel-24kc-musl
status: {status}
target: ramips/mt7621
architecture: mipsel
libc: musl
archive_root: mips-toolchain
compiler_triplet: mipsel-router-linux-musl
compiler_prefix: mipsel-router-linux-musl-
sysroot: sysroot
source_lock: mips-toolchain
''')
        return path

    def ax23v_target(self, status="locked"):
        path = self.path / "ax23v-v1.yaml"
        path.write_text(f'''name: ax23v-v1
status: {status}
device_id: tplink-archer-ax23v-v1
platform_target: ramips/mt7621
architecture: mipsel
libc: musl
toolchain: mipsel-24kc-musl
kernel_source_lock: linux
kernel_release: 6.12.0-router
kernel_config_sha256: {"a" * 64}
vermagic: 6.12.0-router mips32r2
hardware_evidence:
  - ax23v-observation-locked
cross_build_authorized: true
image_authorized: false
flash_authorized: false
rf_transmit_authorized: false
''')
        return path

    def test_accepts_exact_locked_mips_toolchain(self):
        result = cross_call("--record", self.record(), "--upstream-dir", self.upstream,
                            "--source-cache", self.cache)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"result": "accepted-for-host-build"', result.stdout)

    def test_rejects_pending_toolchain(self):
        result = cross_call("--record", self.record(status="pending-verification"), "--upstream-dir", self.upstream,
                            "--source-cache", self.cache)
        self.assertEqual(result.returncode, 2)
        self.assertIn("status: locked", result.stderr)

    def test_accepts_locked_ax23v_target_only_when_all_boundaries_match(self):
        result = cross_call("--record", self.record(), "--target-record", self.ax23v_target(),
                            "--upstream-dir", self.upstream, "--source-cache", self.cache)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_pending_ax23v_target(self):
        result = cross_call("--record", self.record(), "--target-record", self.ax23v_target("pending-verification"),
                            "--upstream-dir", self.upstream, "--source-cache", self.cache)
        self.assertEqual(result.returncode, 2)
        self.assertIn("AX23V cross target", result.stderr)

    def test_rejects_host_or_wrong_compiler_triplet(self):
        record = self.record().read_text().replace("mipsel-router-linux-musl\n", "x86_64-linux-gnu\n", 1)
        path = self.path / "wrong.yaml"
        path.write_text(record.replace("name: mipsel-24kc-musl", "name: wrong"))
        result = cross_call("--record", path, "--upstream-dir", self.upstream,
                            "--source-cache", self.cache)
        self.assertEqual(result.returncode, 2)
        self.assertIn("triplet", result.stderr)

    def test_execute_requires_explicit_command(self):
        result = cross_call("--record", self.record(), "--upstream-dir", self.upstream,
                            "--source-cache", self.cache, "--execute")
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a command", result.stderr)

    def test_execute_sets_only_verified_cross_variables(self):
        command = "import os; assert os.environ['CC'].endswith('mipsel-router-linux-musl-gcc'); assert os.environ['SYSROOT'].endswith('/sysroot'); assert os.environ['PKG_CONFIG_DIR'] == ''; assert os.environ['PKG_CONFIG_PATH'] == ''; assert os.environ['PKG_CONFIG_LIBDIR'].startswith(os.environ['SYSROOT'])"
        result = cross_call("--record", self.record(), "--upstream-dir", self.upstream,
                            "--source-cache", self.cache,
                            "--execute", "--", sys.executable, "-c", command)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_execute_cannot_find_host_only_pkg_config_file(self):
        host_pc = self.path / "host-pc"
        host_pc.mkdir()
        (host_pc / "host-only.pc").write_text("Name: host-only\nDescription: host-only fixture\nVersion: 1\n")
        environment = {**os.environ, "PKG_CONFIG_PATH": str(host_pc)}
        result = cross_call("--record", self.record(), "--upstream-dir", self.upstream,
                            "--source-cache", self.cache, "--execute", "--",
                            "pkg-config", "--exists", "host-only", env=environment)
        self.assertEqual(result.returncode, 1, result.stderr)
