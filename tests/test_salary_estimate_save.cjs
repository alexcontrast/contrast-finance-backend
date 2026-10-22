// Regression: system salary rows must never enter the regular estimate API.
const assert=require('node:assert/strict');const vm=require('node:vm');
const {context,itemRecord,functionSource}=require('./test_manager_editor.cjs');
const salary=()=>itemRecord(901,{item_type:'manager_salary',external_name:'ЗП менеджера',external_price:0,external_amount:0,amount_fact:100,sort_order:9999,__dirty_after_save:true});
let passed=0;
async function test(name,fn){await fn();passed++;console.log('PASS '+name);}
(async()=>{
 await test('system salary remains untouched during a regular bulk save',async()=>{
  const c=context([itemRecord(),salary()]);const row=c.getItem(901),before=JSON.stringify(row);
  await c.saveDraftItems(1,{pruneBlankTemps:true});
  assert.equal(c.stats.api.length,0);assert.equal(JSON.stringify(row),before);
  assert(c.getDraftItems(1).includes(row),'salary row was removed from state');
  assert.equal(c.itemNeedsSave(1,row),false);
 });
 await test('direct forced save cannot PATCH salary as a regular item',async()=>{
  const c=context([salary()]),row=c.getItem(901);
  await c.saveSingleDraftItem(1,row,{force:true});await c.performSingleDraftItemSave(1,row,{force:true});
  assert.equal(c.stats.api.length,0);assert.equal(row.sort_order,9999);
 });
 await test('virtual salary with an accidental regular type is also excluded',async()=>{
  const row=itemRecord('manager_salary',{item_type:'regular',is_manager_salary_virtual:true,is_temp:true});
  const c=context([row]);await c.saveDraftItems(1,{pruneBlankTemps:true});assert.equal(c.stats.api.length,0);
 });
 await test('regular edits and coordinator still save alongside a salary',async()=>{
  const c=context([itemRecord(),salary()]);
  c.setDraftItemValue(1,11,'external_name','Новое название');
  c.setDraftItemValue(1,90,'external_amount_admin','100');
  await c.saveDraftItems(1);
  const writes=c.stats.api.filter(x=>x.method==='PATCH');assert.equal(writes.length,2);
  assert(writes.every(x=>['regular','coordinator'].includes(x.payload.item_type)));
  assert(!writes.some(x=>x.url==='/event-items/901'));assert.equal(c.getItem(901).sort_order,9999);
 });
 for(const target of ['draft','review'])await test(`full save action completes to ${target} after salary payment`,async()=>{
  const c=context([itemRecord(),salary()]);
  vm.runInContext(functionSource('setButtonLoading'),c);
  vm.runInContext(functionSource('setManagerSaveError'),c);
  vm.runInContext(functionSource('saveManagerEventQuick'),c);
  c.perfNow=()=>0;c.timedAction=(_label,fn)=>fn();const messages=[];c.showToast=(message)=>messages.push(message);
  c.attachDraftInputs(1);const input=c.field(11,'external_name');input.value='Отредактированный подрядчик';input.fire('input');
  await c.saveManagerEventQuick(1,target,null,'Успешно');
  assert(messages.includes('Успешно'),messages.join('\n'));
  assert(!messages.some(x=>x.includes('Не удалось')));
  assert(!c.stats.api.some(x=>x.url==='/event-items/901'));
  assert(c.stats.api.filter(x=>x.method==='POST'||x.method==='PATCH').every(x=>x.payload?.item_type!=='manager_salary'));
  assert.equal(c.serverEvents.get(1).status,target);assert.equal(c.getItem(901).sort_order,9999);
 });
 console.log(JSON.stringify({passed}));
})().catch(e=>{console.error(e);process.exitCode=1;});
