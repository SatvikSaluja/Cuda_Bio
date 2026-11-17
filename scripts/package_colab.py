"""Archive current source (including uncommitted edits), without committing anything."""
import argparse
from pathlib import Path
import subprocess
import zipfile
p=argparse.ArgumentParser();p.add_argument('--output',default='/tmp/warpalign-colab.zip');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root).decode().split('\0')
with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name in names:
        path=root/name
        if name and path.is_file() and not path.is_symlink():archive.write(path,name)
print(a.output)
