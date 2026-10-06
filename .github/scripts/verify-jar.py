"""Verify the exact distributable, not an old JAR left in build/libs."""
from pathlib import Path
import re
import tomllib
import zipfile


def verify(root=Path('.')):
    props = dict(re.findall(r'(?m)^([a-z_]+)=(.+)$', (root / 'gradle.properties').read_text()))
    version = props['carpet_version'] + '-tick-' + props['tick_version']
    path = root / ('build/libs/neoforge-carpet-' + version + '.jar')
    with zipfile.ZipFile(path) as jar:
        names = jar.namelist()
        assert not any(n.startswith('carpet/') or 'TickGameTests' in n for n in names), 'Development/legacy classes packaged'
        assert 'dev/clark/carpet_tick/compat/CarpetConflictGuard.class' in names, 'Missing conflict guard'
        assert 'neoforge_carpet_tick.refmap.json' in names, 'Missing refmap'
        metadata = tomllib.loads(jar.read('META-INF/mods.toml').decode())
        assert metadata['mods'][0]['version'] == version, 'Metadata version mismatch'
        forge = next(d for d in metadata['dependencies']['neoforge_carpet_tick'] if d['modId'] == 'forge')
        assert forge['mandatory'] and forge['versionRange'] == '[47.1.5,47.2),[47.4.0,47.5)', 'Common loader range mismatch'
    print(str(path) + ': ' + str(path.stat().st_size) + ' bytes; packaging verified')


if __name__ == '__main__':
    verify()
