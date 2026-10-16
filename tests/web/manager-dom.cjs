// Complete shipped index.html + app.js, running against a DOM and deferred fetch.
// This verifies controls and event handlers; jsdom does not test browser paint/CSP.
const {JSDOM, VirtualConsole} = require('jsdom');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(process.argv[2] || '.');
const errors=[];
const virtualConsole=new VirtualConsole();
virtualConsole.on('jsdomError',e=>errors.push(e));
const dom=new JSDOM(fs.readFileSync(path.join(root,'app/web/index.html'),'utf8'), {
  url:'https://finance.test/',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole,
});
const w=dom.window;
w.matchMedia=()=>({matches:false,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
w.ResizeObserver=class {observe(){}unobserve(){}disconnect(){}};
w.alert=()=>{};w.confirm=()=>true;
let releaseCreate;
let nextId=101;
const calls=[];
w.fetch=async(url,opt={})=>{
  const body=opt.body?JSON.parse(opt.body):null;
  calls.push({url,method:opt.method,body});
  if(url==='/events/1/items') {
    await new Promise(resolve=>releaseCreate=resolve);
    return {ok:true,json:async()=>({...body,id:nextId++,event_id:1,updated_at:'2026-10-15T10:00:01',paid_amount:0})};
  }
  if(url.endsWith('/items/bulk-delete')) return {ok:true,json:async()=>({ok:true})};
  throw new Error(`Unexpected fetch ${url}`);
};
w.eval(fs.readFileSync(path.join(root,'app/web/app.js'),'utf8')+'\nwindow.__test={state,getDraftItems,draftKeyForEvent,addDraftRegularPosition,renderManagerEventDetailImpl,saveSingleDraftItem,rerenderCurrentManagerCard,unlockTaxForItem,applyTaxResultToDraftItem,deleteDraftItem,calculateDraftSummaryPreview};');
const c=w.__test;
const event={id:1,manager_id:2,department_id:1,status:'draft',money_status:'waiting_money',client_name:'Клиент',
  title:'Тест',event_date:'2026-10-15',client_calc_type:'cash',manager_percent:21,agency_commission_amount:0,
  simplified_bank_tax_percent:0,updated_at:'2026-10-15T10:00:00'};
const clone=v=>JSON.parse(JSON.stringify(v));
Object.assign(c.state,{token:'isolated',bootstrap:{user:{id:2,name:'Менеджер',role:'manager',department_id:1}},
  selectedManagerEventId:1,currentManagerEvent:event,managerEstimateTab:'internal',managerData:{events:[event]},
  managerDraftEventsById:{'1':event},managerDraftBaseUpdatedAtByEventId:{'1':event.updated_at},
  managerEventPayloadById:{'1':{event:clone(event),items:[],summary:{}}},currentManagerSummary:{},managerPaymentRequests:[]});
w.document.getElementById('dashboardContent').innerHTML='<div id="managerEventDetail"></div>';
const fire=(node,type='input')=>node.dispatchEvent(new w.Event(type,{bubbles:true}));
const field=(id,name)=>w.document.querySelector(`[data-item-id="${id}"][data-item-field="${name}"]`);

(async()=>{
  const item=c.addDraftRegularPosition(1);
  item.external_name='Новая позиция';
  c.state.managerDraftDirtyByEventId['1']=true;
  await c.renderManagerEventDetailImpl(1,{useDraft:true,noLoading:true});
  const input=field(item.id,'external_name');
  input.value='Ведущий';fire(input);
  const pending=c.saveSingleDraftItem(1,item);
  input.value='Ведущий Жандос';fire(input);
  releaseCreate();await pending;
  assert.equal(field(item.id,'external_name'),input,'POST must retain the same live control');
  input.value='Ведущий Әли';fire(input);
  assert.equal(item.external_name,'Ведущий Әли');
  let method=field(item.id,'payment_method');method.value='invoice';fire(method,'change');
  assert.equal(field(item.id,'external_name').value,'Ведущий Әли');
  assert.equal(item.payment_method,'invoice');
  c.applyTaxResultToDraftItem(item,{iin_bin:'770100000001',tax_status:'our_vat',iin_bin_locked:true,vat_amount:0,deduction_amount:0});
  c.rerenderCurrentManagerCard();
  assert.equal(field(item.id,'iin_bin').disabled,true);
  c.unlockTaxForItem(item.id);
  assert.equal(field(item.id,'iin_bin').disabled,false);
  field(item.id,'iin_bin').value='770100000002';fire(field(item.id,'iin_bin'));
  assert.equal(item.iin_bin,'770100000002');
  assert(item.__dirty_after_save);
  const dangerous='"><img src=x onerror="window.exploited=1">';
  item.external_name=dangerous;event.title=dangerous;
  c.rerenderCurrentManagerCard();
  assert.equal(field(item.id,'external_name').value,dangerous);
  assert.equal(w.document.querySelector('img[src="x"]'),null,'names must remain text/values');
  // A deleted row whose creation is already in flight must be deleted remotely too.
  const removed=c.addDraftRegularPosition(1);removed.external_name='Удалить';
  const creation=c.saveSingleDraftItem(1,removed);c.deleteDraftItem(1,removed.id);releaseCreate();await creation;
  assert(calls.some(x=>x.url.endsWith('/items/bulk-delete')&&x.body.item_ids.includes(removed.id)));
  assert(!c.getDraftItems(1).some(x=>x.id===removed.id));
  assert.equal(errors.length,0,errors.map(e=>e.message).join('\n'));
  console.log('DOM: full page initialization, typing during POST, stable row IDs, payment switch, BIN unlock, escaped names, deletion during POST: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>w.close());
