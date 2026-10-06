"""Exercise real Forge discovery with a temporary low-code mod carrying the carpet ID."""
from pathlib import Path
import argparse
import os
import subprocess
import zipfile

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--run-dir', type=Path, default=root / 'run')
options, gradle_args = parser.parse_known_args()
fixture = options.run_dir / 'mods/tick-conflict-test-fixture.jar'
report = root / 'build/reports/conflict-startup.log'
fixture.parent.mkdir(parents=True, exist_ok=True)
report.parent.mkdir(parents=True, exist_ok=True)
if fixture.exists():
    raise RuntimeError('Refusing to overwrite existing fixture path: ' + str(fixture))
try:
    with zipfile.ZipFile(fixture, 'x') as jar:
        jar.writestr('META-INF/mods.toml', '''modLoader="lowcodefml"
loaderVersion="[47,)"
license="MIT"
[[mods]]
modId="carpet"
version="0.0.0-test"
displayName="Carpet Conflict Test Fixture"
''')
    wrapper = str(root / ('gradlew.bat' if os.name == 'nt' else 'gradlew'))
    with report.open('w', encoding='utf-8') as output:
        result = subprocess.run([wrapper, 'runGameTestServer', '--offline', '--no-daemon', '--console=plain', *gradle_args],
                                cwd=root, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    text = report.read_text(encoding='utf-8')
    assert result.returncode != 0, 'Conflicting installation started successfully'
    for message in ('Carpet Conflict Test Fixture', '[carpet]', 'Use the original Carpet mod', 'Remove neoforge-carpet-tick'):
        assert message in text, 'Missing startup conflict diagnostic: ' + message
    assert 'Started game test server' not in text, 'Conflict was detected after server startup'
    print('Real loader conflict startup rejected before server start; see ' + str(report))
finally:
    fixture.unlink(missing_ok=True)
