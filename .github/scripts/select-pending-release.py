"""Retry only an explicitly verified automatic release, never a docs-only update."""
import json
import os
import re
from pathlib import Path
import subprocess
from upstream import git, properties

def select(state, current_version, published_releases, remote_tag, head):
    version = state.get('release_version')
    if not version or current_version != version:
        return None
    tag = 'v1.4.112-tick-' + version
    if any(r['tag_name'] == tag and not r['draft'] for page in published_releases for r in page):
        return None
    return version, remote_tag.split()[0] if remote_tag else head


def main():
    state = json.loads(Path('.github/upstream-state.json').read_text())
    version = state.get('release_version')
    current = properties(Path('gradle.properties').read_text())['tick_version']
    if not version or current != version:
        return
    tag = 'v1.4.112-tick-' + version
    # gh api reports 404 separately; network/auth errors must not be treated as unpublished.
    releases = json.loads(subprocess.check_output(['gh', 'api', '--paginate', '--slurp',
                                                  'repos/{owner}/{repo}/releases?per_page=100']))
    remote = git('.', 'ls-remote', '--tags', 'origin', 'refs/tags/' + tag).strip()
    # Documentation commits after a failed publication must not change its source commit.
    candidate = git('.', 'log', '-1', '--format=%H', '-G', '^tick_version=' + re.escape(version) + '$',
                    '--', 'gradle.properties').strip()
    if not candidate:
        raise ValueError('Cannot locate the committed automatic version bump')
    selected = select(state, current, releases, remote, candidate)
    if selected:
        version, ref = selected
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write('release=' + version + '\nref=' + ref + '\n')


if __name__ == '__main__':
    main()
