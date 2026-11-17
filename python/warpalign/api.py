"""Local API with durable SQLite results and cancellable process-isolated jobs."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import Aligner, __version__
from .benchmark import measure
from .diagnostics import capabilities,studio_directory
from .io import paf
from .store import Store

DATA=Path(os.environ.get('WARPALIGN_DATA_DIR',str(Path.home()/'.local/share/warpalign'))).expanduser()
_store=None
store_lock=threading.Lock()
executor=ThreadPoolExecutor(max_workers=1)
processes={}
process_lock=threading.Lock()
benchmark_lock=threading.Lock()
MAX_UPLOAD=32*1024*1024

def store():
    global _store
    with store_lock:
        if _store is None:_store=Store(DATA/'studio.sqlite3')
    return _store

@asynccontextmanager
async def lifespan(app):
    DATA.mkdir(parents=True,exist_ok=True)
    owner=open(DATA/'service.lock','a+')
    try:
        if os.name=='posix':
            import fcntl
            try:fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Another Studio process owns this data directory')
        store().recover()
        yield
    finally:
        with process_lock:
            for job in store().jobs():
                if job['status'] in ('queued','running'):store().update(job['id'],'interrupted','Service shutting down')
            for proc in processes.values():stop_process(proc)
        owner.close()

app=FastAPI(title='WarpAlign Studio',version=__version__,lifespan=lifespan)

@app.middleware('http')
async def local_only(request: Request,call_next):
    from urllib.parse import urlsplit
    host=request.headers.get('host','').split(':')[0]
    if host not in ('localhost','127.0.0.1','testserver'):
        return JSONResponse({'detail':'Local host required'},status_code=403)
    origin=request.headers.get('origin')
    if origin:
        parsed=urlsplit(origin)
        if parsed.hostname not in ('localhost','127.0.0.1') or parsed.scheme!='http':
            return JSONResponse({'detail':'Cross-origin access denied'},status_code=403)
    return await call_next(request)

@app.get('/api/status')
def status():
    return {**capabilities(),'version':__version__,'data_directory':str(DATA),'storage':'SQLite (local disk)'}

class Options(BaseModel):
    backend: Literal['auto','cpu','cuda']='auto'
    mode: Literal['exact','fast']='exact'
    mismatch: int=Field(4,ge=1,le=1000)
    gap_open: int=Field(6,ge=0,le=1000)
    gap_extend: int=Field(2,ge=1,le=1000)
    bandwidth: int=Field(64,ge=0,le=100000)
    adaptive_band: bool=False
    max_bandwidth: int=Field(4096,ge=0,le=100000)
    memory_limit: int=Field(128*1024**2,ge=65536,le=512*1024**2)
    batch_size: int=Field(16,ge=1,le=256)
    threads: int=Field(1,ge=1,le=8)
    checkpoint_interval: int=Field(0,ge=0,le=4096)
    kind: Literal['pairwise','map']='pairwise'
    preset: Literal['map-ont','map-hifi']='map-ont'
    ambiguous: Literal['literal','wildcard','mismatch']='literal'
    pairing: Literal['order','id']='order'
    allow_fallback: bool=True
    cuda_max_score: int=Field(1024,ge=0,le=1000000)
    timeout_seconds: float=Field(30,gt=0,le=600)
    job_timeout: int=Field(600,ge=1,le=3600)

async def upload(request):
    body=bytearray()
    async for chunk in request.stream():
        if len(body)+len(chunk)>MAX_UPLOAD:raise HTTPException(413,'Combined upload exceeds 32 MiB')
        body.extend(chunk)
    request._body=bytes(body)
    return await request.form()

def stop_process(proc):
    if proc.poll() is None:
        try:
            if os.name=='posix':os.killpg(proc.pid,signal.SIGTERM)
            else:proc.terminate()
        except ProcessLookupError:pass

def run_job(job,directory,options):
    try:
        with process_lock:
            if store().job(job)['status']!='queued':return
            store().update(job,'running')
            proc=subprocess.Popen([sys.executable,'-m','warpalign.worker','--db',str(store().path),'--job',job,'--directory',directory],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=os.name=='posix',env={**os.environ,'TMPDIR':directory,'TEMP':directory,'TMP':directory})
            processes[job]=proc
        try:code=proc.wait(timeout=options.job_timeout)
        except subprocess.TimeoutExpired:
            stop_process(proc)
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            if store().job(job)['status']=='running':store().update(job,'failed','Job deadline exceeded')
        else:
            if code and store().job(job)['status']=='running':store().update(job,'failed',f'Worker exited with status {code}')
    except Exception as error:
        if store().job(job)['status'] not in ('cancelled','complete'):store().update(job,'failed',str(error))
    finally:
        with process_lock:processes.pop(job,None)
        shutil.rmtree(directory,ignore_errors=True)

def submit(options,queries,targets):
    try:Aligner(**{k:v for k,v in options.model_dump().items() if k not in ('kind','preset','batch_size','pairing','job_timeout')})
    except ValueError as error:raise HTTPException(422,str(error))
    if options.backend=='cuda' and not options.allow_fallback and not capabilities()['cuda']:
        raise HTTPException(422,'CUDA is unavailable and CPU fallback is disabled')
    if options.kind=='map' and not capabilities()['minimap2']:
        raise HTTPException(422,'Install minimap2 before using reference refinement')
    job=uuid.uuid4().hex
    with process_lock:
        if benchmark_lock.locked():raise HTTPException(409,'Wait for the measurement to finish before submitting an alignment')
        try:store().create(job,options.model_dump())
        except ValueError as error:raise HTTPException(429,str(error))
    directory=tempfile.mkdtemp(prefix='warpalign-',dir=DATA)
    try:
        (Path(directory)/'queries').write_bytes(queries)
        (Path(directory)/'targets').write_bytes(targets)
        executor.submit(run_job,job,directory,options)
    except Exception as error:
        store().update(job,'failed',str(error));shutil.rmtree(directory,ignore_errors=True);raise
    return {'id':job}

@app.post('/api/jobs',status_code=202)
async def create_job(request: Request):
    form=await upload(request)
    try:
        options=Options.model_validate_json(str(form.get('options','{}')))
        for name in ('queries','targets'):
            if not hasattr(form.get(name),'read'):raise ValueError(f'Missing {name} upload')
        return submit(options,await form['queries'].read(),await form['targets'].read())
    except (ValueError,TypeError) as error:raise HTTPException(422,str(error))
    finally:await form.close()

@app.post('/api/demo',status_code=202)
def demo():
    return submit(Options(),b'>demo-match\nACGTACGT\n>demo-indel\nACGTAAAACGT\n>demo-mismatch\nAACCGGTT\n',b'>target-match\nACGTACGT\n>target-indel\nACGTACGT\n>target-mismatch\nAATCGGTT\n')

@app.get('/api/jobs')
def list_jobs():return store().jobs()

def job_or_404(job):
    try:return store().job(job)
    except KeyError:raise HTTPException(404,'Unknown job')

@app.get('/api/jobs/{job}')
def get_job(job: str,offset: int=0,limit: int=200,search: str='',sort: str='query_id',descending: bool=False):
    j=job_or_404(job)
    try:total,rows=store().results(job,max(0,offset),min(max(limit,1),500),search,sort,descending)
    except ValueError as error:raise HTTPException(422,str(error))
    return {**j,'results':rows,'filtered_total':total}

@app.get('/api/jobs/{job}/results/{index}')
def detail(job: str,index: int):
    job_or_404(job)
    try:return store().detail(job,index)
    except KeyError:raise HTTPException(404,'Unknown alignment')

@app.post('/api/jobs/{job}/cancel')
def cancel(job: str):
    with process_lock:
        if job_or_404(job)['status'] in ('queued','running'):
            store().update(job,'cancelled','Cancelled by user')
            if job in processes:stop_process(processes[job])
    return job_or_404(job)

@app.get('/api/jobs/{job}/download')
def download(job: str,format: Literal['jsonl','paf']='jsonl'):
    if job_or_404(job)['status']!='complete':raise HTTPException(409,'Only completed jobs can be downloaded')
    def generate():
        for row in store().export(job):
            yield (paf(row) if format=='paf' else json.dumps(row))+'\n'
    return StreamingResponse(generate(),media_type='text/plain',headers={'Content-Disposition':f'attachment; filename="warpalign-{job}.{format}"'})

@app.delete('/api/jobs')
def clear_jobs():store().clear();return {'ok':True}

class Experiment(BaseModel):
    length: int=Field(1000,ge=10,le=10000)
    batch_size: int=Field(4,ge=1,le=16)
    bandwidth: int=Field(64,ge=0,le=1000)
    mode: Literal['exact','fast']='exact'
    backend: Literal['cpu','auto','cuda']='cpu'
    error_rate: float=Field(.01,ge=0,le=.1)
    indel_rate: float=Field(.005,ge=0,le=.05)
    repeats: int=Field(3,ge=1,le=7)
    seed: int=1729

@app.post('/api/benchmarks')
def experiment(options: Experiment):
    with process_lock:
        if not benchmark_lock.acquire(blocking=False):raise HTTPException(429,'Another measurement is running')
        if any(j['status'] in ('running','queued') for j in store().jobs()):
            benchmark_lock.release()
            raise HTTPException(409,'Wait for alignment jobs to finish before measuring')
    try:
        row=measure(**options.model_dump(),timeout_seconds=10)
        store().measurement(row);return row
    except (ValueError,RuntimeError) as error:raise HTTPException(422,str(error))
    finally:benchmark_lock.release()

@app.get('/api/benchmarks')
def get_measurements():return store().measurements()

web=studio_directory()
if (web/'index.html').is_file():app.mount('/',StaticFiles(directory=web,html=True),name='studio')

def main():
    import uvicorn
    parser=argparse.ArgumentParser(description='Local WarpAlign Studio')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    if not 1<=args.port<=65535:parser.error('port must be in 1..65535')
    if not (web/'index.html').is_file():
        print('Studio bundle missing. Run npm ci && npm run build in apps/studio or set WARPALIGN_STUDIO_DIST.',file=sys.stderr)
    print(f'Open http://localhost:{args.port} · local data: {DATA}',flush=True)
    uvicorn.run('warpalign.api:app',host='127.0.0.1',port=args.port)

if __name__=='__main__':main()
