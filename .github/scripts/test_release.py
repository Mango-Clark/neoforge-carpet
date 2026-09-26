import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import upstream as u

SCRIPTS = Path(__file__).parent.resolve()
spec = importlib.util.spec_from_file_location('pending', SCRIPTS / 'select-pending-release.py')
pending = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pending)
verify_spec = importlib.util.spec_from_file_location('gametests', SCRIPTS / 'verify-gametests.py')
gametests = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(gametests)


class EvidenceTests(unittest.TestCase):
    def test_loading_failure_is_not_a_passing_suite(self):
        with self.assertRaises(ValueError):
            gametests.verify('has failed to load correctly\nBUILD SUCCESSFUL')

    def test_all_required_tests_must_run(self):
        with self.assertRaises(ValueError):
            gametests.verify('All 0 required tests passed')
        self.assertEqual(gametests.verify('All 3 required tests passed :)'), 3)


class PublicationTests(unittest.TestCase):
    def test_docs_only_never_starts_release(self):
        self.assertIsNone(pending.select({}, '1.0.0', [], '', 'head'))

    def test_retry_uses_existing_immutable_tag(self):
        self.assertEqual(pending.select({'release_version': '1.0.1'}, '1.0.1', [], 'tagged-sha refs/tags/v1', 'new-head'),
                         ('1.0.1', 'tagged-sha'))

    def test_published_version_not_replaced(self):
        releases = [[{'tag_name': 'v1.4.112-tick-1.0.1', 'draft': False}]]
        self.assertIsNone(pending.select({'release_version': '1.0.1'}, '1.0.1', releases, '', 'head'))

    def test_draft_is_retried(self):
        releases = [[{'tag_name': 'v1.4.112-tick-1.0.1', 'draft': True}]]
        self.assertEqual(pending.select({'release_version': '1.0.1'}, '1.0.1', releases, '', 'head'), ('1.0.1', 'head'))

    def test_new_manual_version_is_not_automatic_retry(self):
        self.assertIsNone(pending.select({'release_version': '1.0.1'}, '1.1.0', [], '', 'head'))


class VersionGateTests(unittest.TestCase):
    def setUp(self):
        bash = Path('C:/Program Files/Git/bin/bash.exe') if os.name == 'nt' else Path(shutil.which('bash') or '/missing')
        if not bash.exists():
            self.skipTest('Git Bash required for release gate tests')
        self.bash = str(bash)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        u.git(self.root, 'init')
        self.props = self.root / 'gradle.properties'
        self.props.write_text('carpet_version=1.4.112\ntick_version=1.0.0\n')
        u.git(self.root, 'add', '.')
        u.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'baseline')
        self.before = u.git(self.root, 'rev-parse', 'HEAD').strip()

    def run_gate(self, event='push', version=''):
        output = self.root / 'outputs'
        output.write_text('')
        env = dict(os.environ, EVENT_NAME=event, GITHUB_EVENT_BEFORE=self.before,
                   INPUT_TICK_VERSION=version, GITHUB_OUTPUT=str(output))
        result = subprocess.run([self.bash, (SCRIPTS / 'check-release-version.sh').as_posix()],
                                cwd=self.root, env=env, text=True, capture_output=True)
        return result, output.read_text()

    def test_unchanged_version_skips(self):
        result, output = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('changed=true', output)

    def test_increasing_version_releases(self):
        self.props.write_text('carpet_version=1.4.112\ntick_version=1.0.1\n')
        result, output = self.run_gate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('changed=true', output)

    def test_decreasing_version_rejected(self):
        self.props.write_text('carpet_version=1.4.112\ntick_version=0.9.9\n')
        result, output = self.run_gate()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('changed=true', output)

    def test_manual_version_cannot_override_checkout(self):
        result, output = self.run_gate('workflow_dispatch', '1.0.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('changed=true', output)

    def test_leading_zero_patch_rejected(self):
        result, _ = self.run_gate('workflow_dispatch', '1.0.01')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
