const {JSDOM}=require('jsdom');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||'.');
const dom=new JSDOM(fs.readFileSync(path.join(root,'app/web/index.html'),'utf8'),{url:'https://finance.test/',runScripts:'outside-only',pretendToBeVisual:true});
const w=dom.window;w.matchMedia=()=>({matches:false,addListener(){},addEventListener(){}});w.ResizeObserver=class{observe(){}disconnect(){}};
const alerts=[];w.alert=m=>alerts.push(m);w.confirm=()=>true;
let mode='not_found',release;let requests=0;
w.fetch=async(url,opt={})=>{
 if(url.endsWith('/tax/check')){
  requests++;if(mode==='pending')await new Promise(r=>release=r);
  const status=mode==='pending'?'our_no_vat':'not_found';
  return {ok:true,json:async()=>({item_id:11,iin_bin:'770100000001',iin_bin_locked:status!=='not_found',tax_check_status:status,
   vat_amount:0,deduction_amount:0,updated_at:'2026-10-16T10:00:01',event_updated_at:'2026-10-16T10:00:01',
   message:status==='not_found'?'КГД не нашёл БИН/ИИН':'Test / ОУР без НДС'})};
 }
 throw new Error(`Unexpected ${url}`);
};
w.eval(fs.readFileSync(path.join(root,'app/web/app.js'),'utf8')+'\nwindow.__test={state,getDraftItems,renderManagerEventDetailImpl,checkTaxForItem,markDraftItemSaved,renderPaymentExtraFields,selectedPaymentItem,checkPaymentInvoiceBin};');
const c=w.__test;
const event={id:1,manager_id:2,department_id:1,status:'draft',money_status:'waiting_money',client_name:'Test',title:'Test',event_date:'2026-10-16',client_calc_type:'cash',manager_percent:21,updated_at:'2026-10-16T10:00:00'};
const item={id:11,event_id:1,item_type:'regular',external_name:'Test',external_price:100,external_quantity:1,external_days:1,external_amount:100,
 amount_fact:50,payment_method:'invoice',iin_bin:'770100000001',iin_bin_locked:false,tax_check_status:null,vat_amount:0,deduction_amount:0,sort_order:0,updated_at:event.updated_at};
const coord={...item,id:90,item_type:'coordinator',external_name:'Координатор',payment_method:null,iin_bin:null,external_price:0,external_amount:0,amount_fact:0,sort_order:-100};
Object.assign(c.state,{token:'isolated',bootstrap:{user:{id:2,role:'manager',department_id:1}},selectedManagerEventId:1,currentManagerEvent:event,
 managerEstimateTab:'internal',managerData:{events:[event]},managerDraftEventsById:{'1':event},managerDraftBaseUpdatedAtByEventId:{'1':event.updated_at},
 managerEventPayloadById:{'1':{event:{...event},items:[{...coord},{...item}],summary:{}}},currentManagerSummary:{},managerPaymentRequests:[]});
w.document.getElementById('dashboardContent').innerHTML='<div id="managerEventDetail"></div>';
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 c.getDraftItems(1,[coord,item]);
 await c.renderManagerEventDetailImpl(1,{useDraft:true,noLoading:true});
 const draft=c.getDraftItems(1).find(x=>x.id===11);c.markDraftItemSaved(draft);
 let btn=w.document.querySelector('[data-check-tax-item="11"]');btn.click();await tick();await tick();
 assert.equal(requests,1);let feedback=w.document.querySelector('tr[data-event-item-row="11"] .tax-check-feedback');
 assert.match(feedback.textContent,/не нашёл/);assert(feedback.classList.contains('is-error'));
 assert.equal(w.document.querySelector('[data-item-id="11"][data-item-field="iin_bin"]').disabled,false);
 mode='pending';btn=w.document.querySelector('[data-check-tax-item="11"]');btn.click();await tick();await tick();
 assert.equal(requests,2);assert(w.document.querySelector('[data-check-tax-item="11"]').disabled);
 assert.match(feedback.textContent,/Проверяем/);
 c.state.managerEstimateTab='external';c.state.managerEstimateTab='internal';await c.renderManagerEventDetailImpl(1,{useDraft:true,noLoading:true});
 assert(w.document.querySelector('[data-check-tax-item="11"]').disabled,'busy state survives rerender');
 release();await tick();await tick();
 assert(w.document.querySelector('[data-unlock-tax-item="11"]'),'success shows unlock action');
 assert.match(w.document.querySelector('tr[data-event-item-row="11"] .tax-check-feedback').textContent,/ОУР/);
 assert.equal(alerts.length,0);assert(!w.document.querySelector('[data-auth-mode="accountant"]'));
 // Reuse the same live row in the payment dialog after a successful check.
 draft.iin_bin_locked=false;draft.tax_check_status=null;delete draft.__tax_check_message;
 c.state.currentManagerEvent.status='review';c.state.managerEventPayloadById['1'].event.status='review';
 const modal=w.document.createElement('div');modal.innerHTML='<select id="paymentItemSelect"><option value="11">Test</option></select><select id="paymentMethodSelect"><option value="invoice">Invoice</option></select><input id="paymentAmountInput" value="25"><div id="paymentPositionInfo"></div><div id="paymentExtraFields"></div><button id="paymentCreateBtn">Создать</button><div id="paymentMessage"></div>';
 w.document.body.appendChild(modal);c.renderPaymentExtraFields(1);
 mode='not_found';w.document.getElementById('paymentCheckBinBtn').click();await tick();await tick();
 assert.match(w.document.getElementById('paymentMessage').textContent,/не нашёл/);
 assert.equal(w.document.getElementById('paymentCheckBinBtn').disabled,false);
 assert.equal(w.document.getElementById('paymentBinInput').disabled,false);
 mode='pending';w.document.getElementById('paymentCheckBinBtn').click();await tick();await tick();
 assert(w.document.getElementById('paymentCreateBtn').disabled);
 w.document.getElementById('paymentAmountInput').value='30';
 release();await tick();await tick();
 assert(w.document.getElementById('paymentCheckBinBtn').disabled);
 assert(w.document.getElementById('paymentBinInput').disabled);
 assert.equal(w.document.getElementById('paymentAmountInput').value,'30','late amount edit was overwritten');
 assert.equal(w.document.getElementById('paymentCreateBtn').disabled,false);
 console.log('DOM BIN: first-click not-found feedback, editable BIN, visible pending state, rerender protection, success, login tabs PASS');
 w.close();
})().catch(e=>{console.error(e);w.close();process.exitCode=1;});
