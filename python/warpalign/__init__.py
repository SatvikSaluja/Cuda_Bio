"""Exact global affine WFA. A gap costs open + length*extend."""
from concurrent.futures import ThreadPoolExecutor
import os
import time
from ._native import Config, Result, ResourceError, Aligner as _Aligner
__version__ = "1.0.0"
FIELDS = "query_id target_id score edit_distance cigar query_start query_end target_start target_end matches mismatches insertions deletions backend execution_time heuristic_used cpu_fallback fallback_reason has_traceback bandwidth heuristic_retries wavefront_bytes gpu_memory_bytes timing_scope".split()

class Aligner:
    def __init__(self, backend="auto", mode="exact", mismatch=4, gap_open=6, gap_extend=2,
                 bandwidth=64, ambiguous="literal", memory_limit=512*1024**2,
                 score_only=False, allow_fallback=True, timeout_seconds=0, threads=1, cuda_max_score=1024, checkpoint_interval=0, adaptive_band=False, max_bandwidth=4096):
        if not isinstance(threads, int) or not 1 <= threads <= 64:
            raise ValueError('threads must be an integer in [1, 64]')
        self.threads = threads
        if not isinstance(cuda_max_score,int) or not 0<=cuda_max_score<=1000000:raise ValueError('invalid cuda_max_score')
        self.cuda_max_score=cuda_max_score
        self.options = {k:v for k,v in locals().copy().items() if k not in ('self','threads','cuda_max_score')}
        self._impl = self._native(self.options)

    @staticmethod
    def _native(options):
        config=Config()
        for key,value in options.items():
            setattr(config,key,value)
        return _Aligner(config)

    def _cuda_results(self,queries,targets):
        self._cuda_attempted=False
        if self.options['backend']=='cpu':return None
        try:
            if os.environ.get('WARPALIGN_EXPERIMENTAL_CUDA')!='1':
                raise RuntimeError('Experimental CUDA is not enabled')
            from . import _cuda
            if getattr(_cuda,'api_version',0)!=2:raise RuntimeError('Rebuild the CUDA extension for this WarpAlign version')
            if not _cuda.available():raise RuntimeError('No compatible CUDA device')
            if self.options['mode']!='exact':raise RuntimeError('CUDA supports exact alignment only')
            self._cuda_attempted=True
            start=time.perf_counter()
            o=self.options
            args=(queries,targets,o['mismatch'],o['gap_open'],o['gap_extend'],o['ambiguous'],o['memory_limit'],self.cuda_max_score)
            results=[]
            if o['score_only']:
                scores=_cuda.scores(*args)
                for q,t,score in zip(queries,targets,scores):
                    r=Result();r.score=score;r.query_end=len(q);r.target_end=len(t);r.has_traceback=False;r.backend='cuda';results.append(r)
            else:
                for row in _cuda.alignments(*args):
                    r=Result()
                    for key,value in row.items():setattr(r,key,value)
                    results.append(r)
            elapsed=time.perf_counter()-start
            for r in results:
                r.execution_time=elapsed/max(1,len(results));r.timing_scope="amortized_batch_wall";r.gpu_memory_bytes=_cuda.last_arena_bytes()
            return results
        except (ImportError,RuntimeError) as error:
            if (self.options['backend']=='cuda' or self._cuda_attempted) and not self.options['allow_fallback']:
                raise ResourceError(str(error)) from error
            self._fallback_reason=str(error)
            return None

    def align(self, query: str, target: str, query_id: str = "", target_id: str = "") -> Result:
        results=self.align_batch([query],[target])
        result=results[0];result.query_id=query_id;result.target_id=target_id;return result

    def align_batch(self, queries: list[str], targets: list[str]) -> list[Result]:
        if len(queries)!=len(targets):raise ValueError('batch lengths differ')
        if not queries:return []
        gpu=self._cuda_results(queries,targets)
        if gpu is not None:return gpu
        if self.threads==1 or len(queries)<2:
            results=self._impl.align_batch(queries,targets)
        else:
            workers=min(self.threads,len(queries))
            worker=self._native({**self.options,'memory_limit':self.options['memory_limit']//workers})
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results=list(pool.map(lambda pair:worker.align(*pair),zip(queries,targets)))
        if self.options['backend']=='cuda' or getattr(self,'_cuda_attempted',False):
            for r in results:
                r.cpu_fallback=True;r.fallback_reason=getattr(self,'_fallback_reason',r.fallback_reason)
        return results

def as_dict(result: Result) -> dict:
    data={key:getattr(result,key) for key in FIELDS}
    if result.backend=='cpu':data['gpu_memory_bytes']=None
    if not result.has_traceback:
        for key in ('edit_distance','matches','mismatches','insertions','deletions'):
            data[key]=None
    return data
