import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {compileMapping,parseDocument,MappingError} from './engine.mjs';

const fixtures=JSON.parse(readFileSync(new URL('../tests/json-fixtures.json',import.meta.url),'utf8'));
for(const fixture of fixtures) test(`shared JSON / ${fixture.name}`,()=>{
  const plan=compileMapping(fixture.from,fixture.to,{validate:fixture.validate});
  if(fixture.error) assert.throws(()=>plan.apply(fixture.input),MappingError);
  else assert.deepEqual(JSON.parse(JSON.stringify(plan.apply(fixture.input))),fixture.expected);
});

test('snapshots isolate templates and repeated calls',()=>{
  const from=['x'],to={list:['x']},plan=compileMapping(from,to);
  from.push('new');to.list.push('new');const first=plan.apply([7]);first.list.push(9);
  assert.deepEqual(JSON.parse(JSON.stringify(plan.apply([7]))),{list:[7]});
});
test('duplicate sample warning and first match',()=>{
  const plan=compileMapping(['x','x'],['x']);assert.equal(plan.warnings.length,1);assert.deepEqual(plan.apply([1,2]),[1]);
});
test('rejects non-JSON custom objects, holes and accessors',()=>{
  assert.throws(()=>compileMapping(new Date(),[]),MappingError);
  assert.throws(()=>compileMapping(new Array(2),[]),MappingError);
  let ran=false;const x={get hidden(){ran=true;return 'x';}};
  assert.throws(()=>compileMapping(x,[]),MappingError);assert.equal(ran,false);
});
test('rejects cycles and excessive depth / size',()=>{
  const x=[];x.push(x);assert.throws(()=>compileMapping(x,[]),/循环/);
  let deep='x';for(let i=0;i<66;i++)deep=[deep];assert.throws(()=>compileMapping(deep,[]),/64/);
  assert.throws(()=>compileMapping(Array(10001).fill(0),[]),/节点/);
  assert.throws(()=>parseDocument(' '.repeat(200001)),/字符/);
});
test('JSON parser rejects invalid numbers, code and unsafe integer precision',()=>{
  for(const text of ['NaN','Infinity','[1,]','(()=>1)()','9007199254740992']) assert.throws(()=>parseDocument(text),MappingError);
});
test('bounds repeated output before stringify',()=>{
  assert.throws(()=>compileMapping(['x'],Array(9999).fill('x')).apply(['a'.repeat(50000)]),/预算/);
});
test('output key must remain string and prototype names remain data',()=>{
  assert.throws(()=>compileMapping(['x'],{x:1}).apply([2]),/字符串/);
  const source=parseDocument('{"__proto__":"x"}');const result=compileMapping(['token'],source).apply([5]);
  assert.equal(Object.getPrototypeOf(result),null);assert.equal(Object.prototype.polluted,undefined);
});
