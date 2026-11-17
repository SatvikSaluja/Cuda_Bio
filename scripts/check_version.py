"""Check release versions without importing the compiled extension."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def version():
    def match(path,pattern):
        found=re.search(pattern,(ROOT/path).read_text(),re.M)
        if not found:raise ValueError(f'Missing version in {path}')
        return found.group(1)
    expected=match('pyproject.toml',r'^version = "([^"]+)"')
    package=json.loads((ROOT/'apps/studio/package.json').read_text())
    lock=json.loads((ROOT/'apps/studio/package-lock.json').read_text())
    actual={
        'Python':match('python/warpalign/__init__.py',r'^__version__ = "([^"]+)"'),
        'CMake':match('CMakeLists.txt',r'project\(WarpAlign VERSION (\S+)'),
        'Citation':match('CITATION.cff',r'^version: (\S+)'),
        'Studio':package['version'], 'npm lock':lock['version'],
        'npm root package':lock['packages']['']['version'],
    }
    if not re.fullmatch(r'\d+\.\d+\.\d+',expected):raise ValueError('Expected stable MAJOR.MINOR.PATCH version')
    for name,value in actual.items():
        if value!=expected:raise ValueError(f'{name} version {value} differs from {expected}')
    if f'# WarpAlign v{expected}' not in (ROOT/'RELEASE_NOTES.md').read_text():raise ValueError('Release notes version mismatch')
    return expected

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tag');a=p.parse_args()
    current=version()
    if a.tag and a.tag!='v'+current:p.error(f'Tag must be v{current}')
    print(current)
