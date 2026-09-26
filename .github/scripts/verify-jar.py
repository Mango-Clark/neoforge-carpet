"""Verify the exact distributable, not an old JAR left in build/libs."""
from pathlib import Path
import re
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
        assert 'version="' + version + '"' in jar.read('META-INF/mods.toml').decode(), 'Metadata version mismatch'
    print(str(path) + ': ' + str(path.stat().st_size) + ' bytes; packaging verified')


if __name__ == '__main__':
    verify()
