"""Disposable job process: cancellation can stop native alignment and its mapper."""
import argparse
from pathlib import Path
from . import Aligner
from .cli import pair_rows
from .mapping import map_reads
from .store import Store

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--job',required=True);p.add_argument('--directory',required=True);a=p.parse_args()
    store=Store(a.db);options=store.job(a.job)['options'];directory=Path(a.directory)
    try:
        aligner=Aligner(**{k:v for k,v in options.items() if k not in ('kind','preset','batch_size','pairing','job_timeout','demo')})
        rows=pair_rows(directory/'queries',directory/'targets',aligner,options['batch_size'],pairing=options['pairing']) if options['kind']=='pairwise' else map_reads(directory/'targets',directory/'queries',aligner,options['preset'])
        for row in rows:store.append(a.job,row)
        if options.get('demo'):
            from .benchmark import measure
            for length in (100,500,1000):
                row=measure(length=length,batch_size=1,repeats=3,error_rate=.01,indel_rate=.005,backend='cpu',timeout_seconds=5)
                row['demo_job']=a.job;store.measurement(row)
        if store.job(a.job)['status']=='running':store.update(a.job,'complete')
    except Exception as error:
        if store.job(a.job)['status']=='running':store.update(a.job,'failed',str(error))

if __name__=='__main__':main()
