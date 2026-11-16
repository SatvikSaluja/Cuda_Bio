"""Loopback-only local service. Jobs and uploaded sequences stay in local memory/tempfiles."""
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import Aligner
from .benchmark import measure, hardware
from .cli import pair_rows
from .mapping import map_reads

app=FastAPI(title='WarpAlign Studio',version='0.1.0')
executor=ThreadPoolExecutor(max_workers=1)
lock=threading.Lock()
jobs={}
measurements=[]
MAX_UPLOAD=32*1024*1024

@app.middleware('http')
async def local_only(request: Request, call_next):
    host=request.headers.get('host','').split(':')[0]
    if host not in ('127.0.0.1','localhost','testserver'):
        return JSONResponse({'detail':'Local host required'},status_code=403)
    origin=request.headers.get('origin')
    if origin and origin not in ('http://127.0.0.1:8000','http://localhost:8000','http://127.0.0.1:5173','http://localhost:5173'):
        return JSONResponse({'detail':'Cross-origin access denied'},status_code=403)
    return await call_next(request)

@app.get('/api/status')
def status():
    return dict(cpu=True,cuda=False,gpu=None,cuda_version=None,minimap2=shutil.which('minimap2') is not None,
                backend='CPU WFA',cuda_status='Experimental score kernel; not validated or enabled',hardware=hardware())

class Options(BaseModel):
    backend: str='auto'
    mode: str='exact'
    mismatch: int=Field(4,ge=1,le=1000)
    gap_open: int=Field(6,ge=0,le=1000)
    gap_extend: int=Field(2,ge=1,le=1000)
    bandwidth: int=Field(64,ge=0,le=100000)
    memory_limit: int=Field(128*1024**2,ge=1024,le=512*1024**2)
    batch_size: int=Field(16,ge=1,le=256)
    kind: str='pairwise'
    preset: str='map-ont'

async def upload(request):
    # Stream and cap total bytes before multipart parsing, including chunked requests.
    body=bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body)>MAX_UPLOAD:raise HTTPException(413,'Combined upload exceeds 32 MiB')
    request._body=bytes(body)
    return await request.form()

def update(job,**values):
    with lock:jobs[job].update(values)

def run_job(job,directory,options):
    try:
        update(job,status='running')
        config=options.model_dump(exclude={'kind','preset','batch_size'})
        aligner=Aligner(**config)
        q=Path(directory)/'queries';t=Path(directory)/'targets'
        rows=pair_rows(q,t,aligner,options.batch_size) if options.kind=='pairwise' else map_reads(t,q,aligner,options.preset)
        for row in rows:
            with lock:
                if len(jobs[job]['results'])>=10000:raise ValueError('Studio limit: 10000 result rows; use CLI for larger jobs')
                jobs[job]['results'].append(row);jobs[job]['completed']+=1
        update(job,status='complete')
    except Exception as error:
        update(job,status='failed',error=str(error))
    finally:
        shutil.rmtree(directory,ignore_errors=True)

@app.post('/api/jobs',status_code=202)
async def create_job(request: Request):
    form=await upload(request)
    try:
        options=Options.model_validate_json(str(form.get('options','{}')))
        Aligner(**options.model_dump(exclude={'kind','preset','batch_size'}))
        if options.kind not in ('pairwise','map'):raise ValueError('Invalid job kind')
        if options.preset not in ('map-ont','map-hifi'):raise ValueError('Invalid preset')
        for name in ('queries','targets'):
            if not hasattr(form.get(name),'read'):raise ValueError(f'Missing {name} upload')
    except (ValueError,TypeError) as error:raise HTTPException(422,str(error))
    with lock:
        if sum(j['status'] in ('queued','running') for j in jobs.values())>=4:raise HTTPException(429,'Local job queue is full')
        if len(jobs)>=20:raise HTTPException(429,'Clear completed jobs in Settings before submitting more')
        job=uuid.uuid4().hex;jobs[job]=dict(id=job,status='queued',completed=0,results=[],options=options.model_dump())
    directory=tempfile.mkdtemp(prefix='warpalign-')
    try:
        for name in ('queries','targets'):(Path(directory)/name).write_bytes(await form[name].read())
        executor.submit(run_job,job,directory,options)
    except Exception:
        shutil.rmtree(directory,ignore_errors=True)
        with lock:jobs.pop(job,None)
        raise
    return {'id':job}

@app.get('/api/jobs')
def list_jobs():
    with lock:return [{k:v for k,v in j.items() if k!='results'} for j in jobs.values()]

@app.get('/api/jobs/{job}')
def get_job(job: str,offset: int=0,limit: int=200):
    with lock:
        if job not in jobs:raise HTTPException(404,'Unknown job')
        j=jobs[job]
        return {**j,'results':j['results'][max(0,offset):max(0,offset)+min(max(limit,1),500)]}

@app.get('/api/jobs/{job}/download')
def download(job: str):
    with lock:
        if job not in jobs:raise HTTPException(404,'Unknown job')
        if jobs[job]['status']!='complete':raise HTTPException(409,'Only completed jobs can be downloaded')
        return JSONResponse(jobs[job],headers={'Content-Disposition':f'attachment; filename="warpalign-{job}.json"'})

@app.delete('/api/jobs')
def clear_jobs():
    with lock:
        for job in list(jobs):
            if jobs[job]['status'] not in ('queued','running'):del jobs[job]
    return {'ok':True}

class Experiment(BaseModel):
    length: int=Field(1000,ge=10,le=10000)
    batch_size: int=Field(4,ge=1,le=16)
    bandwidth: int=Field(64,ge=0,le=1000)
    mode: str='exact'
    backend: str='cpu'

@app.post('/api/benchmarks')
def experiment(options: Experiment):
    try:
        row=measure(**options.model_dump())
    except (ValueError,RuntimeError) as error:raise HTTPException(422,str(error))
    with lock:measurements.append(row)
    return row

@app.get('/api/benchmarks')
def get_measurements():
    with lock:return list(measurements)

# A built React bundle is served on the same loopback origin as the API.
web=Path(os.environ.get('WARPALIGN_STUDIO_DIST', str(Path.cwd()/'apps/studio/dist')))
if not web.is_dir():
    web=Path(__file__).resolve().parents[2]/'apps/studio/dist'
if web.is_dir():app.mount('/',StaticFiles(directory=web,html=True),name='studio')

def main():
    import uvicorn
    uvicorn.run('warpalign.api:app',host='127.0.0.1',port=8000)

if __name__=='__main__':main()
