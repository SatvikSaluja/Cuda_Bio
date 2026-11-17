"""Run real release checks; blocked checks never count as passes (exit 2).

Install .[studio,test,docs] and frontend/browser dependencies first. WFA2 is
optional via --wfa2-root; its checkout and compiler output remain separate.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='benchmarks/results/release-validation')
    p.add_argument('--wfa2-root',type=Path)
    p.add_argument('--checks',default='cuda,docs,browser,external')
    args=p.parse_args();output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    checks=args.checks.split(',')
    if set(checks)-{'cuda','docs','browser','external'}:p.error('Unknown check')
    records=[]
    def record(name,status,reason='',**kw):
        records.append(dict(check=name,status=status,reason=reason,**kw));print(f'{name}: {status}: {reason}',flush=True)
    def run(name,command,cwd=ROOT,env=None,timeout=1800):
        start=time.perf_counter()
        with (output/f'{name}.log').open('w') as log:
            try:r=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout)
            except (OSError,subprocess.TimeoutExpired) as e:
                record(name,'failed',str(e),command=command);return False
        ok=r.returncode==0
        record(name,'passed' if ok else 'failed',command=command,exit_code=r.returncode,seconds=time.perf_counter()-start,log=f'{name}.log')
        return ok
    if 'cuda' in checks:
        missing=[c for c in ('nvcc','nvidia-smi','compute-sanitizer','cmake') if not shutil.which(c)]
        if missing:record('cuda','blocked','Missing commands: '+', '.join(missing))
        else:run('cuda',['bash','scripts/validate_cuda.sh'])
    if 'docs' in checks:
        if importlib.util.find_spec('mkdocs') is None:record('docs','blocked','Install the docs extra: python -m pip install -e .[docs]')
        else:run('docs',[sys.executable,'-m','mkdocs','build','--strict','--site-dir',str(output/'site')])
    if 'external' in checks:
        root=args.wfa2_root.resolve() if args.wfa2_root else None
        if not root or not (root/'wavefront/wavefront_align.h').exists():record('external','blocked','Supply --wfa2-root pointing to a built WFA2-lib checkout')
        elif not shutil.which('cc'):record('external','blocked','C compiler is unavailable')
        else:
            revision=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True)
            dirty=subprocess.run(['git','-C',str(root),'status','--porcelain'],capture_output=True,text=True)
            if revision.returncode or dirty.returncode or dirty.stdout.strip():record('external','blocked','WFA2 must be a clean revision-identifiable checkout')
            else:
                adapter=str(output/'wfa2-adapter')
                if run('wfa2-build',['cc','-O3','-fopenmp','-I'+str(root),'benchmarks/adapters/wfa2.c','-L'+str(root/'lib'),'-Wl,-rpath,'+str(root/'lib'),'-lwfa','-lm','-o',adapter]):
                    for mode in ('high','ultralow'):
                        run('wfa2-'+mode,[sys.executable,'benchmarks/scripts/compare_external.py','--baseline-version',revision.stdout.strip(),'--output',str(output/f'wfa2-{mode}.json'),adapter,mode])
    if 'browser' in checks:
        node=shutil.which('node')
        if not node:record('browser','blocked','Node.js is unavailable')
        elif not (ROOT/'apps/studio/dist/index.html').exists():record('browser','blocked','Build Studio first: cd apps/studio && npm ci && npm run build')
        else:
            probe=subprocess.run([node,'--input-type=module','-e',"await import('playwright')"],cwd=ROOT/'tests/e2e',capture_output=True,text=True)
            if probe.returncode:record('browser','blocked','Install tests/e2e dependencies and Chromium; see tests/e2e/README.md')
            else:
                try:
                    with socket.socket() as listener:
                        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
                except OSError as error:
                    record('browser','blocked','Cannot create local socket: '+str(error));port=None
                if port is not None:
                    with tempfile.TemporaryDirectory(prefix='warpalign-browser-') as data:
                        env={**os.environ,'WARPALIGN_DATA_DIR':data,'WARPALIGN_BASE_URL':f'http://127.0.0.1:{port}'}
                        with (output/'browser-server.log').open('w') as log:
                            server=subprocess.Popen([sys.executable,'-m','warpalign.api','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                            try:
                                ready=False
                                for _ in range(100):
                                    if server.poll() is not None:break
                                    try:
                                        with urllib.request.urlopen(env['WARPALIGN_BASE_URL']+'/api/status',timeout=.5) as r:ready=r.status==200
                                    except OSError:pass
                                    if ready:break
                                    time.sleep(.1)
                                if ready:run('browser',[node,'tests/e2e/studio.mjs'],env=env,timeout=120)
                                else:record('browser','failed','Local service did not become ready; see browser-server.log')
                            finally:
                                if server.poll() is None:
                                    server.terminate()
                                    try:server.wait(timeout=10)
                                    except subprocess.TimeoutExpired:server.kill();server.wait()
    report=dict(python=sys.version,command=sys.argv,records=records)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return 1 if any(r['status']=='failed' for r in records) else 2 if any(r['status']=='blocked' for r in records) else 0

if __name__=='__main__':sys.exit(main())
