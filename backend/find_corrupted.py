from pathlib import Path
import sys

site_packages = Path(sys.prefix) / 'Lib' / 'site-packages'

for dist_info in sorted(site_packages.glob('*.dist-info')):
    entry_points = dist_info / 'entry_points.txt'
    if entry_points.exists():
        try:
            entry_points.read_text('utf-8')
            print(f'OK: {dist_info.name}')
        except UnicodeDecodeError:
            print(f'CORRUPTED: {dist_info.name}')
            # Fix it
            entry_points.write_text('', encoding='utf-8')
            print(f'FIXED: {dist_info.name}')

