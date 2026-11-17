"""Build the native package, optionally including a prebuilt Studio bundle."""
from pathlib import Path
import os
import shutil
from setuptools import setup, Extension
from setuptools.command.build_py import build_py

class BuildPython(build_py):
    def run(self):
        super().run()
        target=Path(self.build_lib)/'warpalign/_studio'
        if target.exists():shutil.rmtree(target)
        bundle=Path('apps/studio/dist')
        if (bundle/'index.html').is_file():
            shutil.copytree(bundle,Path(self.build_lib)/'warpalign/_studio',dirs_exist_ok=True)

# Standard isolated builds install pybind11 from pyproject.toml. An explicit
# header path permits offline packagers to use an already installed SDK.
headers=os.environ.get('PYBIND11_INCLUDE_DIR')
if not headers:
    import pybind11
    headers=pybind11.get_include()
setup(ext_modules=[Extension('warpalign._native',['python/bindings.cpp'],include_dirs=['include',headers],depends=[str(p) for p in Path('include/warpalign').glob('*.hpp')],
                             language='c++',extra_compile_args=['/std:c++17','/O2'] if os.name=='nt' else ['-std=c++17','-O3'])],
      cmdclass={'build_py':BuildPython})
