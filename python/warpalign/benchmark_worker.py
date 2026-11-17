"""One benchmark configuration per process, allowing honest process peak RSS."""
import json
import platform
import sys
from .benchmark import measure

def main():
    options=json.loads(sys.argv[1])
    row=measure(**options)
    try:
        import resource
        value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        row['process_peak_rss_bytes']=int(value if platform.system()=='Darwin' else value*1024)
    except ImportError:row['process_peak_rss_bytes']=None
    row['rss_scope']='Entire isolated worker, including imports, generation, reference and warm-up'
    print(json.dumps(row))

if __name__=='__main__':main()
