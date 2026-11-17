"""Inspect installed capabilities without confusing hardware with backend support."""
from functools import lru_cache
from pathlib import Path
import importlib.util
import os
import platform
import shutil
import subprocess

def command(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None

def studio_directory():
    configured = os.environ.get('WARPALIGN_STUDIO_DIST')
    if configured:
        return Path(configured).expanduser()
    candidates = [Path(__file__).parent / '_studio', Path.cwd() / 'apps/studio/dist',
                  Path(__file__).resolve().parents[2] / 'apps/studio/dist']
    return next((p for p in candidates if (p / 'index.html').is_file()), candidates[0])

@lru_cache(maxsize=1)
def capabilities():
    devices = command(['nvidia-smi', '--query-gpu=name,memory.total,driver_version,compute_cap', '--format=csv,noheader'])
    if not devices:devices=command(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'])
    nvcc = command(['nvcc', '--version'])
    cuda_extension = importlib.util.find_spec('warpalign._cuda') is not None
    experimental = os.environ.get('WARPALIGN_EXPERIMENTAL_CUDA') == '1'
    available=False
    if cuda_extension and experimental:
        try:
            from . import _cuda
            available=getattr(_cuda,'api_version',0)==2 and _cuda.available()
        except (ImportError,RuntimeError):pass
    return dict(cpu=True, native_extension=importlib.util.find_spec('warpalign._native') is not None,
                gpu=devices, cuda_version=nvcc, cuda=available,
                cuda_extension=cuda_extension, experimental_cuda_enabled=experimental,
                cuda_status='Experimental CUDA scoring; full traceback uses CPU' if cuda_extension and experimental else 'CUDA disabled; install optional extension and explicitly opt in',
                minimap2=shutil.which('minimap2') is not None, minimap2_version=command(['minimap2', '--version']),
                cmake=shutil.which('cmake'), nvcc=shutil.which('nvcc'), python=platform.python_version(),
                studio_built=(studio_directory()/'index.html').is_file(), studio_directory=str(studio_directory()),
                backend='CPU WFA', platform=platform.platform())
