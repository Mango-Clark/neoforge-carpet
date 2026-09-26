"""Version-gated, fail-closed upstream tracking. Standard library only; never runs upstream code."""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STATE = Path('.github/upstream-state.json')
RULES = Path('.github/upstream-rules.json')
REPOSITORY = 'chililisoup/neoforge-carpet'
BRANCHES = ('master', '1.20.1')
BEGIN = '<!-- upstream-status:start -->'
END = '<!-- upstream-status:end -->'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode('utf-8')


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def properties(text):
    return dict(re.findall(r'^\s*([a-z_]+)\s*=\s*([^\s#]+)', text, re.M))


def snapshot(repo, ref):
    sha = git(repo, 'rev-parse', ref).strip()
    property_text = git(repo, 'show', sha + ':gradle.properties')
    props = properties(property_text)
    for key in ('carpet_version', 'port_version'):
        if not re.fullmatch(r'[0-9A-Za-z.+_-]+', props.get(key, '')):
            raise ValueError('Missing or unsafe upstream version: ' + key)
    # Conservative closure: ALL source/resources and unknown files are relevant.
    # Only explicit documentation/CI exclusions and the two version properties are ignored.
    tree = {}
    for entry in git(repo, 'ls-tree', '-rz', sha).split('\0'):
        if not entry:
            continue
        metadata, path = entry.split('\t', 1)
        if path.startswith(('docs/', '.github/')) or path.endswith('.md') or path in ('LICENSE', '.gitignore', '.gitattributes'):
            continue
        mode, kind, blob = metadata.split()
        if path == 'gradle.properties':
            # Preserve unknown properties/formatting rather than silently ignoring dependencies.
            relevant = re.sub(r'(?m)^[ \t]*(?:carpet_version|port_version)[ \t]*=.*(?:\n|$)', '', property_text)
            blob = digest(relevant)
        tree[path] = mode + ':' + kind + ':' + blob
    return {'version': props['carpet_version'] + '-port-' + props['port_version'],
            'sha': sha, 'fingerprint': digest(json.dumps(tree, sort_keys=True)), 'files': tree}


def local_fingerprint(root):
    files = {}
    for path in sorted((root / 'src/tick').rglob('*')):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = digest(path.read_text(encoding='utf-8'))
    for name in ('build.gradle', 'settings.gradle'):
        files[name] = digest((root / name).read_text(encoding='utf-8'))
    props = properties((root / 'gradle.properties').read_text(encoding='utf-8'))
    files['gradle.properties'] = {k: v for k, v in props.items() if k != 'tick_version'}
    return digest(json.dumps(files, sort_keys=True))


def failure(state, branch, version, reason):
    item = {'branch': branch, 'version': version, 'reason': reason}
    if not any(all(old.get(k) == v for k, v in item.items()) for old in state['failures']):
        state['failures'].append(dict(item, date=datetime.date.today().isoformat()))


def bump(version, level):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Invalid tick_version')
    parts = list(map(int, version.split('.')))
    index = {'major': 0, 'minor': 1, 'patch': 2}[level]
    parts[index] += 1
    for i in range(index + 1, 3):
        parts[i] = 0
    return '.'.join(map(str, parts))


def apply_rule(root, entry, candidate, rules):
    old = entry['reviewed']
    matches = [r for r in rules if r['from_sha'] == old['sha'] and r['to_sha'] == candidate['sha']]
    if len(matches) != 1:
        raise ValueError('No unique reviewed transformation rule for this exact commit pair')
    rule = matches[0]
    if rule['base_local_sha256'] != local_fingerprint(root):
        raise ValueError('Local implementation differs from the reviewed rule baseline')
    if rule['from_fingerprint'] != old['fingerprint'] or rule['to_fingerprint'] != candidate['fingerprint']:
        raise ValueError('Upstream source fingerprint mismatch')
    if rule.get('bump') not in ('patch', 'minor', 'major') or not rule.get('summary', '').strip():
        raise ValueError('Rule needs a reviewed SemVer classification and changelog summary')
    edits = {}
    for edit in rule['edits']:
        relative = Path(edit['path'])
        path = (root / relative).resolve()
        allowed = (root / 'src/tick').resolve()
        if not path.is_relative_to(allowed) or not path.is_file() or relative.as_posix().endswith('TickGameTests.java'):
            raise ValueError('Rule target must be an existing tick runtime file')
        if path in edits:
            raise ValueError('Duplicate rule target')
        before = path.read_text(encoding='utf-8')
        if digest(before) != edit['before_sha256'] or digest(edit['content']) != edit['after_sha256']:
            raise ValueError('Rule content fingerprint mismatch')
        if before == edit['content']:
            raise ValueError('Rule has no runtime change')
        edits[path] = edit['content']
    if not edits:
        raise ValueError('Empty port rule')
    props_path = root / 'gradle.properties'
    props_text = props_path.read_text(encoding='utf-8')
    props = properties(props_text)
    if props['carpet_version'] != '1.4.112':
        raise ValueError('carpet_version must stay fixed')
    version = bump(props['tick_version'], rule['bump'])
    changelog = root / 'CHANGELOG.md'
    text = changelog.read_text(encoding='utf-8')
    if '## [Unreleased]\n' not in text:
        raise ValueError('Missing Unreleased changelog section')
    # All preconditions have passed before the first write.
    for path, content in edits.items():
        path.write_text(content, encoding='utf-8')
    start = text.index('## [Unreleased]\n') + len('## [Unreleased]\n')
    end = text.find('\n## ', start)
    end = len(text) if end == -1 else end
    section = text[start:end]
    bullet = '- ' + rule['summary'].strip() + '\n'
    if '### Changed\n' in section:
        section = section.replace('### Changed\n', '### Changed\n\n' + bullet, 1)
    else:
        section = '\n### Changed\n\n' + bullet + section
    text = text[:start] + section + text[end:]
    changelog.write_text(text, encoding='utf-8')
    props_path.write_text(re.sub(r'(?m)^tick_version=.*$', 'tick_version=' + version, props_text), encoding='utf-8')
    entry['pending'] = candidate
    entry['status'] = 'awaiting-build-and-gametests'
    return version


def process(root, state, snapshots, rules):
    release = None
    for branch in BRANCHES:
        candidate = snapshots[branch]
        entry = state['branches'].setdefault(branch, {})
        observed = entry.get('observed')
        if observed and observed['version'] == candidate['version'] and observed['sha'] != candidate['sha']:
            # Same-version commits are intentionally deferred until the next version change.
            candidate = observed
        entry['observed'] = candidate
        if branch == 'master':
            entry['status'] = 'informational-only'
            continue
        if not entry.get('reviewed'):
            entry['status'] = 'baseline-review-required'
            failure(state, branch, candidate['version'], 'Initial correspondence must be reviewed before automatic ports')
            continue
        previous = entry['reviewed']
        if candidate['version'] == previous['version']:
            if entry.get('status') == 'validation-failed':
                entry['status'] = ('verified' if entry.get('applied') == previous else 'no-runtime-change')
            continue
        entry['changed_paths'] = sorted(path for path in previous['files'].keys() | candidate['files'].keys()
                                        if previous['files'].get(path) != candidate['files'].get(path))
        if previous['fingerprint'] == candidate['fingerprint']:
            entry['reviewed'] = candidate
            entry['status'] = 'no-runtime-change'
            continue
        try:
            release = apply_rule(root, entry, candidate, rules)
        except (ValueError, KeyError) as error:
            entry['status'] = 'port-review-required'
            failure(state, branch, candidate['version'], str(error))
    return release


def label(snapshot):
    if not snapshot:
        return 'Not verified'
    return snapshot['version'] + ' (`' + snapshot['sha'][:12] + '`)'


def block(state):
    lines = [BEGIN, '## Upstream tracking status', '',
             'Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). '
             'Detected versions are not a compatibility claim.', '',
             '| Branch | Latest detected | Reviewed | Applied and verified | Status |',
             '| --- | --- | --- | --- | --- |']
    for branch in BRANCHES:
        entry = state['branches'].get(branch, {})
        lines.append('| ' + ' | '.join((branch, label(entry.get('observed')), label(entry.get('reviewed')),
                                        label(entry.get('applied')), entry.get('status', 'Not checked'))) + ' |')
    lines += ['', 'Failure history: ' + str(len(state['failures'])) + ' distinct event(s). '
              'Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.', END]
    return '\n'.join(lines)


def render(root, state, check=False):
    expected = block(state)
    changed = []
    # Only repository documents; never caches, generated files, or upstream checkout docs.
    paths = git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z', '*.md').split('\0')
    for name in sorted(set(filter(None, paths))):
        path = root / name
        text = path.read_text(encoding='utf-8')
        if (BEGIN in text) != (END in text) or text.count(BEGIN) > 1 or text.count(END) > 1:
            raise ValueError('Malformed generated document block: ' + name)
        if BEGIN in text:
            updated = text[:text.index(BEGIN)] + expected + text[text.index(END) + len(END):]
        else:
            updated = text.rstrip() + '\n\n' + expected + '\n'
        if updated != text:
            changed.append(name)
            if not check:
                path.write_text(updated, encoding='utf-8')
    if check and changed:
        raise ValueError('Stale upstream documentation: ' + ', '.join(changed))


def fetch(root):
    cache = root / 'build/upstream-cache'
    if not (cache / 'HEAD').exists():
        cache.mkdir(parents=True, exist_ok=True)
        git(cache, 'init', '--bare')
    git(cache, 'fetch', '--no-tags', 'https://github.com/' + REPOSITORY + '.git',
        '+refs/heads/master:refs/heads/master', '+refs/heads/1.20.1:refs/heads/1.20.1')
    return {branch: snapshot(cache, branch) for branch in BRANCHES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['scan', 'render', 'check', 'finalize', 'fail', 'approve-baseline'])
    parser.add_argument('--sha', help='Explicit reviewed 1.20.1 baseline commit')
    parser.add_argument('--reason', default='Build or GameTests failed; runtime changes were discarded')
    args = parser.parse_args()
    state = read_json(ROOT / STATE)
    release = None
    if args.command == 'scan':
        try:
            snapshots = fetch(ROOT)
            release = process(ROOT, state, snapshots, read_json(ROOT / RULES)['rules'])
        except (subprocess.CalledProcessError, OSError, ValueError) as error:
            # Keep the last known versions; an unavailable source is never "no update".
            failure(state, 'fetch', 'unknown', type(error).__name__ + ': upstream fetch/snapshot failed')
            write_json(ROOT / STATE, state)
            render(ROOT, state)
            raise
    elif args.command == 'approve-baseline':
        entry = state['branches'].get('1.20.1', {})
        observed = entry.get('observed')
        if not observed or args.sha != observed['sha'] or entry.get('reviewed'):
            raise ValueError('Provide the exact initial detected SHA after manually verifying correspondence')
        entry.update(reviewed=copy.deepcopy(observed), applied=copy.deepcopy(observed),
                     local_sha256=local_fingerprint(ROOT), status='baseline-approved')
    elif args.command in ('finalize', 'fail'):
        entry = state['branches'].get('1.20.1', {})
        pending = entry.pop('pending', None)
        if args.command == 'finalize' and pending:
            entry.update(reviewed=pending, applied=pending, local_sha256=local_fingerprint(ROOT), status='verified')
            state['release_version'] = properties((ROOT / 'gradle.properties').read_text())['tick_version']
        elif args.command == 'fail':
            entry['status'] = 'validation-failed'
            failure(state, '1.20.1', label(entry.get('observed')), args.reason)
    if args.command != 'check':
        write_json(ROOT / STATE, state)
    render(ROOT, state, check=args.command == 'check')
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a', encoding='utf-8') as stream:
            stream.write('release=' + (release or '') + '\n')


if __name__ == '__main__':
    main()
