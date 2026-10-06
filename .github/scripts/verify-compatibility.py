"""Verify common JAR contents against both loaders and preserve each run's evidence."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time

from upstream import properties
from verify_compatibility_support import jar_contents


ROOT = Path(__file__).resolve().parents[2]
MATRIX = [('forge', '47.4.0'), ('forge', '47.4.20'),
          ('neoforge', '47.1.5'), ('neoforge', '47.1.106')]


def main():
    props = properties((ROOT / 'gradle.properties').read_text())
    artifact = ROOT / ('build/libs/neoforge-carpet-' + props['carpet_version']
                       + '-tick-' + props['tick_version'] + '.jar')
    reports = ROOT / 'build/reports/compatibility'
    reports.mkdir(parents=True, exist_ok=True)
    canonical = reports / artifact.name
    wrapper = str(ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew'))
    expected = None
    for loader, version in MATRIX:
        target = reports / (loader + '-' + version)
        target.mkdir(parents=True, exist_ok=True)
        run_dir = Path('build/compatibility-runs') / (loader + '-' + version)
        flags = ['-Ptick_loader=' + loader, '-P' + loader + '_version=' + version,
                 '-Ptick_test_run_dir=' + run_dir.as_posix()]
        started = time.time_ns()
        (target / 'success.txt').unlink(missing_ok=True)
        print('Validating ' + loader + ' ' + version, flush=True)
        try:
            with (target / 'build.log').open('w', encoding='utf-8') as output:
                subprocess.run([wrapper, 'build', 'runGameTestServer', '--no-daemon',
                                '--console=plain', *flags], cwd=ROOT, stdout=output,
                               stderr=subprocess.STDOUT, check=True, timeout=1200)
            subprocess.run([sys.executable, '.github/scripts/verify-gametests.py',
                            str(run_dir / 'logs/latest.log')], cwd=ROOT, check=True)
            shutil.copy2(ROOT / 'build/reports/gametest-success.log', target / 'gametest-success.log')
            subprocess.run([sys.executable, '.github/scripts/verify-jar.py'], cwd=ROOT, check=True)
            contents = jar_contents(artifact)
            if expected is None:
                shutil.copy2(artifact, canonical)
                expected = contents
            else:
                changed = sorted(k for k in set(expected) | set(contents)
                                 if expected.get(k) != contents.get(k))
                if changed:
                    raise RuntimeError('Common JAR differs across loaders: ' + ', '.join(changed))
            subprocess.run([sys.executable, '.github/scripts/test-conflict-startup.py',
                            '--run-dir', str(ROOT / run_dir), *flags],
                           cwd=ROOT, check=True)
            (target / 'success.txt').write_text('GameTests, packaging, common contents and conflict rejection passed\n')
        finally:
            for source in (ROOT / run_dir / 'logs/latest.log', ROOT / 'build/reports/conflict-startup.log'):
                if source.exists() and source.stat().st_mtime_ns >= started:
                    shutil.copy2(source, target / source.name)
    shutil.copy2(canonical, artifact)
    print('All four loader targets passed; common artifact: ' + str(artifact), flush=True)


if __name__ == '__main__':
    main()
