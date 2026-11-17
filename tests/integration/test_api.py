import asyncio
import json
import httpx
from warpalign.api import app

# An in-process ASGI client avoids binding sockets. The periodic timer also lets
# sandboxed event loops poll when cross-thread self-pipe notifications are denied.
def run(scenario):
    async def execute():
        async def tick():
            while True:
                await asyncio.sleep(.01)
        heartbeat=asyncio.create_task(tick())
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as client:
                await asyncio.wait_for(scenario(client),10)
        finally:
            heartbeat.cancel()
    asyncio.run(execute())

def test_real_job_and_benchmark():
    async def scenario(client):
        assert (await client.get('/api/status')).json()['cpu']
        response=await client.post('/api/jobs',files={'queries':('q.fa',b'>q\nACGT\n'),'targets':('t.fa',b'>t\nACGTT\n')},data={'options':json.dumps({'backend':'cuda'})})
        assert response.status_code==202,response.text
        jid=response.json()['id']
        for _ in range(100):
            job=(await client.get('/api/jobs/'+jid)).json()
            if job['status'] in ('complete','failed'):break
            await asyncio.sleep(.01)
        assert job['status']=='complete',job
        assert job['results'][0]['score']==8
        assert job['results'][0]['cpu_fallback']
        assert (await client.get(f'/api/jobs/{jid}/download')).status_code==200
        experiment=(await client.post('/api/benchmarks',json={'length':100,'batch_size':2})).json()
        assert experiment['seconds']>0 and experiment['score_agreement']==1
        assert experiment['gpu_memory_bytes'] is None
        assert (await client.delete('/api/jobs')).status_code==200
    run(scenario)

def test_reject_remote_and_invalid():
    async def scenario(client):
        assert (await client.get('/api/status',headers={'host':'evil.example'})).status_code==403
        assert (await client.post('/api/jobs',headers={'origin':'https://evil.example'})).status_code==403
        assert (await client.post('/api/jobs',data={'options':'{}'})).status_code==422
        assert (await client.post('/api/benchmarks',json={'length':1000000})).status_code==422
    run(scenario)

def test_detail_demo_and_cancel():
    async def scenario(client):
        created=await client.post('/api/demo');assert created.status_code==202
        jid=created.json()['id']
        for _ in range(300):
            job=(await client.get('/api/jobs/'+jid)).json()
            if job['status'] in ('complete','failed'):break
            await asyncio.sleep(.01)
        assert job['status']=='complete',job
        assert job['completed']==3 and 'query_sequence' not in job['results'][0]
        searched=(await client.get('/api/jobs/'+jid+'?search=indel')).json()
        assert searched['filtered_total']==1
        index=searched['results'][0]['result_index']
        detail=(await client.get(f'/api/jobs/{jid}/results/{index}')).json()
        assert detail['query_sequence']=='ACGTAAAACGT'
        assert (await client.get(f'/api/jobs/{jid}/download?format=paf')).status_code==200
        assert (await client.post(f'/api/jobs/{jid}/cancel')).json()['status']=='complete'
        # Cancel a genuinely submitted large job. Both queued and running are valid states.
        response=await client.post('/api/jobs',files={'queries':('q.fa',b'>q\n'+b'A'*50000+b'\n'),'targets':('t.fa',b'>t\n'+b'C'*50000+b'\n')})
        assert response.status_code==202
        cancelled=await client.post('/api/jobs/'+response.json()['id']+'/cancel')
        assert cancelled.json()['status']=='cancelled'
        assert (await client.get('/api/jobs/'+response.json()['id']+'/download')).status_code==409
    run(scenario)

def test_measurement_excludes_new_alignment_jobs():
    from warpalign.api import benchmark_lock
    async def scenario(client):
        benchmark_lock.acquire()
        try:
            assert (await client.post('/api/demo')).status_code==409
        finally:benchmark_lock.release()
    run(scenario)
