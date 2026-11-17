"""Live container/service smoke test. Run explicitly, not through pytest."""
import json
import time
import urllib.request

def request(path,method='GET'):
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/'+path,method=method),timeout=10) as response:
        return json.load(response)

if __name__=='__main__':
    assert request('status')['cpu']
    job=request('demo','POST')['id']
    for _ in range(120):
        state=request('jobs/'+job)
        if state['status'] not in ('queued','running'):break
        time.sleep(.5)
    assert state['status']=='complete',state
    result=request(f'jobs/{job}/results/1')
    assert result['insertions']>0 and result['deletions']>0 and result['mismatches']>0
    assert len([r for r in request('benchmarks') if r.get('demo_job')==job])==3
    print('Container API, real native alignment and demo measurements passed')
