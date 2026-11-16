import test from 'node:test';import assert from 'node:assert/strict';import {viewport,alignmentLength} from '../src/alignment.mjs';
test('SAM insertion and deletion orientation',()=>{assert.deepEqual(viewport('ACGT','ACT','2=1I1=').map(x=>[x.q,x.t]),[['A','A'],['C','C'],['G','-'],['T','T']]);assert.equal(viewport('ACT','ACGT','2=1D1=',2)[0].q,'-');});
test('long-read viewport remains bounded',()=>{const s='A'.repeat(100000);assert.equal(viewport(s,s,'100000=',95000,80).length,80);assert.equal(alignmentLength('20=5I10D'),35);});
