import test from 'node:test';import assert from 'node:assert/strict';import {viewport,alignmentLength} from '../src/alignment.mjs';
test('SAM insertion and deletion orientation',()=>{assert.deepEqual(viewport('ACGT','ACT','2=1I1=').map(x=>[x.q,x.t]),[['A','A'],['C','C'],['G','-'],['T','T']]);assert.equal(viewport('ACT','ACGT','2=1D1=',2)[0].q,'-');});
test('long-read viewport remains bounded',()=>{const s='A'.repeat(100000);assert.equal(viewport(s,s,'100000=',95000,80).length,80);assert.equal(alignmentLength('20=5I10D'),35);});
import {indexAlignment,indexedViewport} from '../src/alignment.mjs';
test('indexed navigation includes coordinates and variant positions',()=>{const index=indexAlignment('2=1I1=');assert.deepEqual(index.variants,[2]);const cells=indexedViewport('ACGT','ACT',index,2,2);assert.equal(cells[0].tpos,null);assert.equal(cells[1].qpos,3);assert.equal(cells[1].tpos,2);});
test('invalid CIGARs are rejected',()=>{for(const bad of ['x','0=','2=bad','2M'])assert.throws(()=>indexAlignment(bad));});
test('viewport near end of many CIGAR runs preserves query and reference offsets',()=>{const cigar='1=1I1D'.repeat(10000);const index=indexAlignment(cigar);const cells=indexedViewport('A'.repeat(20000),'A'.repeat(20000),index,29997,3);assert.deepEqual(cells.map(x=>x.op),['=','I','D']);assert.equal(cells[0].qpos,19998);assert.equal(cells[2].tpos,19999);});
