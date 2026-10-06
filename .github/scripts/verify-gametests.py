"""Forge may exit zero after a loading failure; require positive GameTest evidence."""
from pathlib import Path
import re
import sys


def verify(text):
    matches = re.findall(r'All (\d+) required tests passed', text)
    if not matches or int(matches[-1]) < 3:
        raise ValueError('Missing evidence that all required GameTests ran and passed')
    if 'has failed to load correctly' in text or re.search(r'\d+ required tests? failed', text):
        raise ValueError('GameTest log contains a loading or required test failure')
    return int(matches[-1])


if __name__ == '__main__':
    log = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('run/logs/latest.log')
    count = verify(log.read_text(encoding='utf-8'))
    Path('build/reports').mkdir(parents=True, exist_ok=True)
    Path('build/reports/gametest-success.log').write_text(log.read_text(encoding='utf-8'), encoding='utf-8')
    print(str(count) + ' required GameTests passed (positive log evidence)')
