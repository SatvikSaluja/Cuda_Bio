import type {Measurement} from '../types';
export function Comparison({rows}:{rows:Measurement[]}){
 const key=(r:Measurement)=>[r.dataset_sha256,r.mode,r.bandwidth,r.score_only||false,r.threads||1].join(':');
 const cpu=new Map(rows.filter(r=>r.backend==='cpu'&&r.cpu_fallback_fraction===0).map(r=>[key(r),r]));
 const pairs=rows.filter(r=>r.backend==='cuda'||r.backend==='cuda+cpu').map(gpu=>({gpu,cpu:cpu.get(key(gpu))})).filter(p=>p.cpu);
 return <section className="panel"><h3>Matched CPU / GPU comparisons</h3><p className="muted">Only identical dataset hashes, modes, bandwidths, output scopes and thread settings are paired. CUDA + CPU includes CPU traceback.</p>{!pairs.length?<p className="empty">No matching CPU and GPU measurements yet. CPU fallback is excluded from GPU comparisons.</p>:<div className="table-scroll"><table><thead><tr><th>Length</th><th>Batch</th><th>GPU path</th><th>CPU median</th><th>GPU median</th><th>Measured ratio</th></tr></thead><tbody>{pairs.map(({gpu,cpu},i)=><tr key={i}><td>{gpu.length}</td><td>{gpu.batch_size}</td><td>{gpu.backend}</td><td>{cpu!.seconds.toFixed(6)} s</td><td>{gpu.seconds.toFixed(6)} s</td><td>{(cpu!.seconds/gpu.seconds).toFixed(2)}× CPU/GPU</td></tr>)}</tbody></table></div>}</section>
}
