import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import upstream as u


class UpstreamTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / 'src/tick/java/Example.java'
        self.runtime.parent.mkdir(parents=True)
        self.runtime.write_text('class Example {}\n')
        for name in ('build.gradle', 'settings.gradle'):
            (self.root / name).write_text('// fixture\n')
        (self.root / 'gradle.properties').write_text('carpet_version=1.4.112\ntick_version=1.0.0\n')
        (self.root / 'CHANGELOG.md').write_text('# Changelog\n\n## [Unreleased]\n')
        (self.root / 'README.md').write_text('# Fixture\n')
        u.git(self.root, 'init')
        self.old = dict(version='1-port-1', sha='a' * 40, fingerprint='old', files={'src/A': 'old'})
        self.new = dict(version='1-port-2', sha='b' * 40, fingerprint='new', files={'src/A': 'new'})
        self.state = {'branches': {'1.20.1': {'observed': copy.deepcopy(self.old),
                                           'reviewed': copy.deepcopy(self.old),
                                           'applied': copy.deepcopy(self.old), 'status': 'verified'}}, 'failures': []}

    def snapshots(self, candidate=None):
        return {'master': copy.deepcopy(self.new), '1.20.1': copy.deepcopy(candidate or self.new)}

    def rule(self):
        return dict(from_sha=self.old['sha'], to_sha=self.new['sha'],
                    from_fingerprint='old', to_fingerprint='new',
                    base_local_sha256=u.local_fingerprint(self.root), bump='patch', summary='Fix tick behavior.',
                    edits=[dict(path='src/tick/java/Example.java', before_sha256=u.digest('class Example {}\n'),
                                content='class Example { int ticks; }\n',
                                after_sha256=u.digest('class Example { int ticks; }\n'))])

    def test_initial_baseline_is_not_verified_or_released(self):
        state = {'branches': {}, 'failures': []}
        self.assertIsNone(u.process(self.root, state, self.snapshots(), []))
        self.assertNotIn('applied', state['branches']['1.20.1'])
        self.assertEqual(state['branches']['1.20.1']['status'], 'baseline-review-required')

    def test_same_version_commits_are_deferred(self):
        candidate = dict(self.new, version=self.old['version'])
        u.process(self.root, self.state, self.snapshots(candidate), [])
        self.assertEqual(self.state['branches']['1.20.1']['observed'], self.old)

    def test_docs_only_does_not_bump_or_claim_applied(self):
        candidate = dict(self.new, fingerprint='old', files=self.old['files'])
        self.assertIsNone(u.process(self.root, self.state, self.snapshots(candidate), []))
        self.assertEqual(self.state['branches']['1.20.1']['applied'], self.old)
        self.assertEqual(self.state['branches']['1.20.1']['reviewed'], candidate)
        self.assertIn('tick_version=1.0.0', (self.root / 'gradle.properties').read_text())

    def test_unknown_change_is_blocked_and_failure_deduplicated(self):
        for _ in range(2):
            u.process(self.root, self.state, self.snapshots(), [])
        self.assertEqual(len(self.state['failures']), 1)
        self.assertEqual(self.state['branches']['1.20.1']['reviewed'], self.old)
        self.assertEqual(self.runtime.read_text(), 'class Example {}\n')

    def test_known_rule_requires_validation_before_applied(self):
        version = u.process(self.root, self.state, self.snapshots(), [self.rule()])
        self.assertEqual(version, '1.0.1')
        entry = self.state['branches']['1.20.1']
        self.assertEqual(entry['applied'], self.old)
        self.assertEqual(entry['pending'], self.new)
        self.assertIn('Fix tick behavior.', (self.root / 'CHANGELOG.md').read_text())

    def test_stale_rule_does_not_modify_files(self):
        rule = self.rule()
        self.runtime.write_text('class Different {}\n')
        self.assertIsNone(u.process(self.root, self.state, self.snapshots(), [rule]))
        self.assertEqual(self.runtime.read_text(), 'class Different {}\n')

    def test_rule_cannot_escape_runtime_directory(self):
        rule = self.rule()
        rule['edits'][0]['path'] = '../../escape'
        self.assertIsNone(u.process(self.root, self.state, self.snapshots(), [rule]))
        self.assertEqual(self.runtime.read_text(), 'class Example {}\n')

    def test_rules_retry_after_review_without_new_version(self):
        u.process(self.root, self.state, self.snapshots(), [])
        self.assertEqual(u.process(self.root, self.state, self.snapshots(), [self.rule()]), '1.0.1')

    def test_document_blocks_are_consistent_and_idempotent(self):
        u.render(self.root, self.state)
        first = (self.root / 'README.md').read_text()
        u.render(self.root, self.state)
        self.assertEqual(first, (self.root / 'README.md').read_text())
        u.render(self.root, self.state, check=True)
        (self.root / 'README.md').write_text(first.replace('verified', 'wrong'))
        with self.assertRaises(ValueError):
            u.render(self.root, self.state, check=True)

    def test_fetch_failure_preserves_last_known_versions(self):
        u.write_json(self.root / u.STATE, self.state)
        with patch.object(u, 'ROOT', self.root), patch.object(u, 'fetch', side_effect=OSError('offline')):
            with patch('sys.argv', ['upstream.py', 'scan']), self.assertRaises(OSError):
                u.main()
        saved = u.read_json(self.root / u.STATE)
        self.assertEqual(saved['branches'], self.state['branches'])
        self.assertEqual(len(saved['failures']), 1)

    def test_finalize_and_validation_failure(self):
        self.state['branches']['1.20.1']['pending'] = self.new
        u.write_json(self.root / u.STATE, self.state)
        with patch.object(u, 'ROOT', self.root), patch('sys.argv', ['upstream.py', 'finalize']):
            u.main()
        saved = u.read_json(self.root / u.STATE)
        self.assertEqual(saved['branches']['1.20.1']['applied'], self.new)
        self.assertEqual(saved['release_version'], '1.0.0')
        with patch.object(u, 'ROOT', self.root), patch('sys.argv', ['upstream.py', 'fail']):
            u.main()
        self.assertEqual(u.read_json(self.root / u.STATE)['branches']['1.20.1']['status'], 'validation-failed')

    def test_semver(self):
        self.assertEqual(u.bump('1.2.3', 'patch'), '1.2.4')
        self.assertEqual(u.bump('1.2.3', 'minor'), '1.3.0')
        self.assertEqual(u.bump('1.2.3', 'major'), '2.0.0')
        with self.assertRaises(ValueError):
            u.bump('1.2.03', 'patch')

    def test_snapshot_covers_indirect_dependencies(self):
        (self.root / 'gradle.properties').write_text('carpet_version=1.4.112\nport_version=1.0.8\nforge_version=47.4.4\n')
        u.git(self.root, 'add', '.')
        u.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'initial')
        before = u.snapshot(self.root, 'HEAD')
        (self.root / 'gradle.properties').write_text('carpet_version=1.4.112\nport_version=1.0.9\nforge_version=47.4.4\n')
        (self.root / 'README.md').write_text('# New docs\n')
        u.git(self.root, 'add', '.')
        u.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'docs/version')
        after = u.snapshot(self.root, 'HEAD')
        self.assertEqual(before['fingerprint'], after['fingerprint'])
        (self.root / 'build.gradle').write_text('// changed dependency\n')
        u.git(self.root, 'add', '.')
        u.git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'dependency')
        self.assertNotEqual(after['fingerprint'], u.snapshot(self.root, 'HEAD')['fingerprint'])


if __name__ == '__main__':
    unittest.main()
