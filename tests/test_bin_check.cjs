// Deferred responses exercise the shipped BIN handlers, not a reimplementation.
const assert = require('node:assert/strict');
const {context,itemRecord}=require('./test_manager_editor.cjs');
const gate=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const tick=()=>new Promise(r=>setImmediate(r));
const bin='770100000001';
const tax=(item,status='our_vat')=>({item_id:item.id,iin_bin:bin,iin_bin_locked:status!=='not_found',tax_check_status:status,
 vat_amount:100,deduction_amount:200,updated_at:'2026-10-16T07:20:00',event_updated_at:'2026-10-16T07:20:00',
 message:status==='not_found'?'КГД не нашёл БИН/ИИН. Проверьте номер.':'Контрагент / ОУР с НДС',contractor_name:'Контрагент'});
const row=()=>itemRecord(11,{payment_method:'invoice',iin_bin:bin});
let passed=0;
async function test(name,fn){await fn();passed++;console.log('PASS '+name);}
(async()=>{
 await test('not found is visible after the first click and remains editable',async()=>{
  const c=context([row()]), item=c.getItem(11);let calls=0;
  c.api=async(u,o)=>{if(u.endsWith('/tax/check')){calls++;return tax(item,'not_found');}return c.baseApi(u,o);};
  await c.checkTaxForItem(11);
  assert.equal(calls,1);assert.equal(item.tax_check_status,'not_found');assert.equal(item.iin_bin_locked,false);
  assert.match(c.taxCheckFeedback(item),/не нашёл/);assert.equal(item.__tax_check_pending,false);
  assert.match(c.taxCheckButtonHtml(item),/danger/);
 });
 await test('technical failure stays visible and cannot lock the BIN',async()=>{
  const c=context([row()]),item=c.getItem(11);
  c.api=async(u,o)=>{if(u.endsWith('/tax/check'))throw new Error('КГД временно недоступен');return c.baseApi(u,o);};
  await c.checkTaxForItem(11);
  assert.match(c.taxCheckFeedback(item),/временно недоступен/);assert.equal(item.tax_check_status,'error');
  assert.equal(item.iin_bin_locked,false);assert.equal(item.deduction_amount,0);
 });
 await test('double click makes one tax request even after DOM rerender',async()=>{
  const c=context([row()]),item=c.getItem(11),g=gate();let calls=0;
  c.api=async(u,o)=>{if(u.endsWith('/tax/check')){calls++;await g.promise;return tax(item);}return c.baseApi(u,o);};
  const a=c.checkTaxForItem(11);await tick();const b=c.checkTaxForItem(11);await tick();
  assert.match(c.taxCheckFeedback(item),/Проверяем/);assert.match(c.taxCheckButtonHtml(item),/disabled/);
  assert.equal(calls,1);g.resolve();await Promise.all([a,b]);assert.equal(item.iin_bin_locked,true);
 });
 await test('autosave waits for tax result and uses its new revision',async()=>{
  const c=context([row()]),item=c.getItem(11),g=gate();let inTax=false,patches=0;
  c.api=async(u,o)=>{
   if(u.endsWith('/tax/check')){inTax=true;await g.promise;inTax=false;return tax(item);}
   if(o?.method==='PATCH'){assert.equal(inTax,false,'PATCH overlapped KGD');patches++;assert.equal(JSON.parse(o.body).expected_updated_at,'2026-10-16T07:20:00');}
   return c.baseApi(u,o);
  };
  const checking=c.checkTaxForItem(11);await tick();
  c.setDraftItemValue(1,11,'external_name','Новое название');const saving=c.saveSingleDraftItem(1,item);await tick();
  assert.equal(patches,0);g.resolve();await Promise.all([checking,saving]);assert.equal(patches,1);
  assert.equal(item.external_name,'Новое название');assert.equal(item.tax_check_status,'our_vat');
 });
 await test('pending temporary POST finishes before tax and no duplicate is created',async()=>{
  const temp=itemRecord('tmp-bin',{is_temp:true,__client_create_token:'bin-token',payment_method:'invoice',iin_bin:bin});
  const c=context([temp]),item=c.getItem('tmp-bin'),g=gate();let creates=0,taxes=0;
  c.api=async(u,o)=>{
   if(u==='/events/1/items'){creates++;await g.promise;return c.baseApi(u,o);}
   if(u.endsWith('/tax/check')){taxes++;assert.match(u,/^\/event-items\/\d+\/tax\/check$/);return tax(item);}
   return c.baseApi(u,o);
  };
  const saving=c.saveSingleDraftItem(1,item);const checking=c.checkTaxForItem('tmp-bin');await tick();assert.equal(taxes,0);
  g.resolve();await Promise.all([saving,checking]);assert.equal(creates,1);assert.equal(taxes,1);assert.equal(item.iin_bin_locked,true);
 });
 await test('new combined check blocks autosave through temporary ID replacement',async()=>{
  const temp=itemRecord('tmp-bin',{is_temp:true,__client_create_token:'bin-token',payment_method:'invoice',iin_bin:bin});
  const c=context([temp]),item=c.getItem('tmp-bin'),g=gate();let combined=0,creates=0;
  c.api=async(u,o)=>{
   if(u==='/events/1/items/tax/check'){combined++;await g.promise;return {item:itemRecord(77,{payment_method:'invoice',iin_bin:bin}),tax:tax({id:77})};}
   if(u==='/events/1/items')creates++;
   // The test's simulated storage needs the newly acknowledged row too.
   if(u==='/event-items/77'&&o?.method==='PATCH')c.serverItems.set(77,itemRecord(77));
   return c.baseApi(u,o);
  };
  const checking=c.checkTaxForItem('tmp-bin');await tick();
  c.setDraftItemValue(1,'tmp-bin','external_name','Изменено во время КГД');const saving=c.saveSingleDraftItem(1,item);
  g.resolve();await Promise.all([checking,saving]);assert.equal(combined,1);assert.equal(creates,0);
  assert.equal(item.external_name,'Изменено во время КГД');assert.equal(item.iin_bin_locked,true);
 });
 await test('changing the BIN discards the previous failure message',async()=>{
  const c=context([row()]),item=c.getItem(11);item.__tax_check_message='Старая ошибка';item.tax_check_status='not_found';
  c.setDraftItemValue(1,11,'iin_bin','770100000002');assert.equal(c.taxCheckFeedback(item),'');
 });
 await test('invalid length gives visible feedback and sends no tax request',async()=>{
  const c=context([row()]),item=c.getItem(11);c.field(11,'iin_bin').value='123';
  await c.checkTaxForItem(11);assert.match(c.taxCheckFeedback(item),/12 цифр/);assert.equal(c.stats.api.length,0);
 });
 console.log(JSON.stringify({passed}));
})().catch(e=>{console.error(e);process.exitCode=1;});
