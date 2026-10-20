// Regression scenarios against the shipped editor functions, with deferred network replies.
// Network, storage and minimal DOM boundaries are simulated. No production calls.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert/strict');
const {performance} = require('perf_hooks');
const {randomUUID} = require('crypto');
const source = fs.readFileSync(path.join(process.argv[2], 'app/web/app.js'), 'utf8');
const results = [];

function functionSource(name) {
  const start = source.search(new RegExp(`^(?:async )?function ${name}\\(`, 'm'));
  assert(start >= 0, `Missing source function ${name}`);
  const next = source.slice(start + 1).search(/^(?:async )?function \w+\(/m);
  return next < 0 ? source.slice(start) : source.slice(start, start + 1 + next);
}
const names = [
  'asNumber','normalizeNumberInput','formatMoney','formatInputNumber','integerInputValue',
  'draftKeyForEvent','cloneItem','generateDraftItemCreateToken','generateDraftTempId',
  'sanitizeDraftItems','compactDraftItems','ensureDraftItemCreateToken','ensureCoordinator',
  'getDraftItems','getDraftDeletedIds','isBlankTemporaryDraftItem','addDraftRegularPosition',
  'roundMoney','financeRate',
  'resolveDraftItemId','materializeDraftItemId','scheduleDraftVisibleCalculations','syncAllVisibleDraftRows',
  'normalizedDraftFieldValue','setDraftItemValue','externalRowAmount','externalItemsTotal',
  'externalAgencyCommissionAmount','internalCommissionValue','internalDeductionValue',
  'internalVatValue','selfEmployedDeductionBase','ensureSelfEmployedItemTax',
  'clearDraftSelfEmployedFields','taxBaseForItem','recalculateCheckedItemTax',
  'activePaymentRequestsForItem','activeInvoicePaymentRequestForItem',
  'itemHasActiveInvoicePaymentRequest','itemHasActiveSelfEmployedPaymentRequest',
  'itemHasActivePaymentRequest','itemHasLockedInvoicePayment','itemHasLockedSelfEmployedPayment',
  'isSimplePaymentMethod','activePaymentRequestMethodsForItem','itemHasOnlyActiveSimplePaymentRequests',
  'itemCanSwitchCashCardMethod','itemPaymentMethodLocked','paymentMethodFromActiveRequest',
  'activeNonSimplePaymentRequestMethodForItem','paymentMethodIsFixed','fixedPaymentMethodForItem',
  'paymentRequestDisplayForItem','paidAmountCellHtml','itemDeleteLockedByPaymentRequest','isCoordinatorItem',
  'isAdminEditingCurrentEvent','isAdminEventEditModeFor','adminCanOverrideItemBin',
  'adminManualTaxOverrideEnabled','isTaxProblem','canEditManagerEvent',
  'calculateDraftSummaryPreview','itemPayloadForSave','draftItemConflictSnapshot',
  'setDraftItemServerSnapshot','sameDraftSnapshotValue','markDraftItemSaved','originalItemForSave',
  'itemNeedsSave','draftItemSaveOperationKey','performSingleDraftItemSave','saveSingleDraftItem',
  'saveDraftItems','deleteDraftItem','managerMonthCacheRecord','patchManagerEventPayloadItems',
  'applyDraftEventRevision','draftEventConflictSnapshot','setDraftEventServerSnapshot',
  'eventPayloadForSave','comparablePayloadString','eventNeedsSave','saveDraftEvent',
  'patchManagerEventLocal','managerAutosaveAllowed','managerAutosaveStorageKey',
  'snapshotManagerDraftForAutosave','storeManagerAutosaveSnapshot','clearManagerAutosaveSnapshot',
  'markManagerDraftChanged','scheduleManagerDraftAutosave','cfGlobalMap',
  'runManagerDraftSaveSerial','refreshManagerEventRevision','notifyManagerEventSaved',
  'managerSaveConflict','flushManagerDraftAutosave','attachDraftInputs',
  'refreshDraftVisibleCalculations','updateInternalRowCells','updateInternalSummaryCards',
  'taxCheckFeedback','taxCheckFeedbackHtml','taxCheckButtonHtml','runDraftItemTaxCheck','checkTaxForItem','updateTaxUiInPlace','unlockTaxForItem','syncDraftItemFromRowBeforeTax','rerenderCurrentManagerCard',
  'applyTaxResultToDraftItem','applyTaxResultPreservingEdits','createDraftItemAndCheckTax','resetManagerDraftFromServer',
  'managerEventHasLocalUnsavedChanges','patchOpenManagerEventPayload','updateCurrentManagerMiniCardLive',
  'rowInput','manualTaxInputHtml','internalFactDisplayValue','renderInternalEstimate',
];

function classList() { return {add(){},remove(){},toggle(){}}; }
function element(attrs = {}, value = '') {
  const node = {attrs:{...attrs},value,disabled:false,listeners:{},classList:classList(),dataset:{},
    textContent:'',style:{},isConnected:true,
    getAttribute(key){return this.attrs[key] ?? null;},
    setAttribute(key,value){this.attrs[key]=String(value);},
    addEventListener(type,fn){(this.listeners[type] ||= []).push(fn);},
    fire(type){for(const fn of [...(this.listeners[type]||[])]) fn({target:this,preventDefault(){},stopPropagation(){}});},
    focus(){},remove(){},appendChild(){},querySelector(){return null;},querySelectorAll(){return []},
  };
  return node;
}
function deferred() { let resolve,reject; const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject}; }
function eventRecord(id=1, updated='2026-10-15T07:00:00') {
  return {id,client_name:`Клиент ${id}`,title:`Мероприятие ${id}`,event_date:'2026-10-15',
    department_id:1,manager_id:2,status:'draft',money_status:'waiting_money',client_calc_type:'cash',
    manager_percent:21,agency_commission_amount:0,agency_commission_spread_enabled:false,
    simplified_bank_tax_percent:0,updated_at:updated};
}
function itemRecord(id=11, values={}) {
  return {id,event_id:1,item_type:'regular',external_name:'Фотограф',external_price:100000,
    external_quantity:1,external_days:1,external_amount:100000,external_note:null,
    amount_fact:50000,paid_amount:0,payment_method:'cash',iin_bin:null,iin_bin_locked:false,
    tax_check_status:null,vat_amount:0,deduction_amount:0,internal_note:null,sort_order:0,
    updated_at:'2026-10-15T07:00:00',is_deleted:false,...values};
}
function coordinator() { return itemRecord(90,{item_type:'coordinator',external_name:'Координатор',external_price:0,
  external_amount:0,amount_fact:0,payment_method:null,sort_order:-100}); }
const clone=value=>JSON.parse(JSON.stringify(value));

function context(items=[itemRecord()], options={}) {
  const stats={calls:{},storageWrites:0,storageBytes:0,raf:0,rafCallbacks:[],domQueries:0,findComparisons:0,htmlWrites:0,api:[]};
  const store=new Map(); const timers=new Map(); let timerId=0; let revision=0;
  const ev=eventRecord();
  const initial=[coordinator(),...items];
  const state={token:'local-audit',bootstrap:{user:{id:2,role:'manager'}},month:'2026-10',selectedManagerEventId:1,
    currentManagerEvent:ev,currentManagerItems:initial,currentManagerSummary:{},managerEstimateTab:'internal',
    managerDraftItemsByEventId:{},managerDraftDeletedByEventId:{},managerDraftEventsById:{'1':ev},
    managerDraftDirtyByEventId:{'1':false},managerDraftGenerationByEventId:{'1':0},
    managerDraftBaseUpdatedAtByEventId:{'1':ev.updated_at},managerDraftAutosaveByEventId:{},
    managerDraftAutosaveTimersByEventId:{},managerEventPayloadById:{'1':{event:clone(ev),items:clone(initial)}},
    managerDashboardBundleCacheByMonth:{},managerPaymentRequests:[],managerData:{events:[clone(ev)]},
  };
  const holder=element(); const card=element(); card.replaceWith=()=>{stats.replacedCard=true;};
  holder.dataset={};holder.querySelector=q=>q==='.manager-event-card'?card:null;
  Object.defineProperty(holder,'innerHTML',{set(v){stats.htmlWrites++;this.html=v;},get(){return this.html||'';}});
  const grid=element();
  Object.defineProperty(grid,'innerHTML',{set(v){stats.htmlWrites++;this.html=v;},get(){return this.html||'';}});
  const metrics=Array.from({length:6},()=>{const n=element();n.querySelector=()=>element();return n;});
  grid.querySelectorAll=()=>metrics;
  const mini=element(); mini.querySelector=()=>null;mini.querySelectorAll=()=>[];
  let fields=[], rows=[];
  const doc={hidden:false,
    getElementById(id){return ['managerEventDetail','eventModalContent'].includes(id)?holder:null;},
    querySelector(q){stats.domQueries++;
      if(q==='.manager-summary-grid-six') return options.grid===false?null:grid;
      if(q.startsWith('[data-manager-event-id=')) return mini;
      const match=q.match(/^tr\[data-event-item-row="([^"]+)"\]$/);
      if(match) return rows.find(r=>r.attrs['data-event-item-row']===match[1])||null;
      return null;
    },
    querySelectorAll(q){stats.domQueries++;
      if(q==='[data-item-field]') return fields.filter(f=>f.attrs['data-item-field']);
      if(q==='[data-event-item-row]') return rows;
      const attr=q.match(/^\[([^=]+)="([^"]+)"\]$/);
      if(attr) return [...fields,...rows].filter(n=>n.attrs[attr[1]]===attr[2]);
      return [];
    },
    createElement(){return {innerHTML:'',firstElementChild:element()};},
  };
  const sandbox={console,Intl,Number,String,Math,Date,JSON,Map,Set,WeakMap,Uint32Array,URL,AbortController,setTimeout,clearTimeout,
    state,CF_PERF_LOGS_ENABLED:false,performance,
    window:{crypto:{randomUUID},performance,location:{origin:'https://local.audit'},
      setTimeout(fn){timers.set(++timerId,fn);return timerId;},clearTimeout(id){timers.delete(id);},
      requestAnimationFrame(fn){stats.raf++;stats.rafCallbacks.push(fn);timers.set(++timerId,fn);},confirm:()=>true,addEventListener(){}},
    localStorage:{getItem:k=>store.get(k)||null,setItem(k,v){stats.storageWrites++;stats.storageBytes+=Buffer.byteLength(v);store.set(k,v);},removeItem:k=>store.delete(k)},
    document:doc,$:id=>doc.getElementById(id),requestAnimationFrame(){stats.raf++;},
    escapeHtml:v=>String(v).replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x])),
    eventDateForInput:v=>String(v||'').slice(0,10),
    getManagerDashboardEvent:id=>state.managerData.events.find(e=>Number(e.id)===Number(id))||null,
    cachedManagerEventPayload:id=>state.managerEventPayloadById[String(id)]||null,
    selfEmployedSurnameFromItem:()=>'',applyEventShareToSummaryValues:x=>x,
    statusLabel:v=>v,eventStatusToneClass:()=>'',eventIsCoauthored:()=>false,
    attachManagerCreateWorkspaceActions(){},attachDraftEventInputs(){},attachCustomerPaymentActions(){},
    scheduleMiniBadgeFit(){stats.raf++;},bindTaxButtons(){},showDraftSavedHint(){},alert(){},
    isItemRevisionConflictError:()=>false,isEventRevisionConflictError:()=>false,
    sortItemsCoordinatorFirst:xs=>xs.slice().sort((a,b)=>(a.item_type==='coordinator'?-1:0)-(b.item_type==='coordinator'?-1:0)),
    internalAgencyCommissionAmount:()=>0,internalSimplifiedMarkupAmount:()=>0,
    summaryNumber:(s,k)=>Number(s?.[k]||0),draggableHandle:()=>'',deleteButtonHtmlForItem:()=>'',
    internalPaymentMethodOptionsHtml:()=>'',formatPlainNumber:v=>String(v),
    selectedSimplePaymentMethodForItem:()=> 'cash',internalTaxesNet:s=>s.taxes_net||0,
    internalVatNet:s=>s.vat_to_pay||0,managerPercentLabel:()=> 'Менеджер',
    customerPaymentMetric:()=>'',metric:(label,v)=>`<div>${label}:${v}</div>`,
    formatDateRu:v=>String(v),customerPaymentLabel:v=>v,
    renderManagerEventCard(event,items){sandbox.rendered=clone({event,items});return '<section></section>';},
    stats,
  };
  const ctx=vm.createContext(sandbox);
  for(const name of names) vm.runInContext(functionSource(name),ctx,{filename:`original:${name}`});
  // The same cache key used in the original program, rather than an assumed ID key.
  state.managerDraftItemsByEventId[ctx.draftKeyForEvent(1)]=initial;
  state.managerDraftDeletedByEventId[ctx.draftKeyForEvent(1)]=[];
  for(const item of initial) if(!item.is_temp && !String(item.id).startsWith('tmp-')) ctx.markDraftItemSaved(item);
  ctx.setDraftEventServerSnapshot(1,ev);
  const serverItems=new Map(initial.filter(x=>!x.is_temp).map(x=>[Number(x.id),clone(x)]));
  const serverEvents=new Map([[1,clone(ev)]]);
  function nextRev(){return `2026-10-15T07:01:${String(++revision).padStart(2,'0')}`;}
  ctx.api=async(url,opt={})=>{
    const method=opt.method||'GET'; const payload=opt.body?JSON.parse(opt.body):null;
    stats.api.push({url,method,payload});
    let m=url.match(/^\/events\/(\d+)(?:\?.*)?$/);
    if(m){const id=Number(m[1]);const e=serverEvents.get(id)||eventRecord(id);
      if(method==='PATCH'){Object.assign(e,payload,{id,updated_at:nextRev()});serverEvents.set(id,e);}return clone(e);}
    m=url.match(/^\/events\/(\d+)\/items$/);
    if(m&&method==='POST'){const id=100+serverItems.size;const item=itemRecord(id,{...payload,event_id:Number(m[1]),updated_at:nextRev()});serverItems.set(id,item);serverEvents.get(Number(m[1])).updated_at=item.updated_at;return clone(item);}
    m=url.match(/^\/event-items\/(\d+)$/);
    if(m&&method==='PATCH'){const item=serverItems.get(Number(m[1]));assert(item,'Unknown simulated row');Object.assign(item,payload,{updated_at:nextRev()});serverEvents.get(item.event_id).updated_at=item.updated_at;return clone(item);}
    if(url.endsWith('/items/bulk-delete')){for(const id of payload.item_ids)serverItems.delete(Number(id));return {ok:true};}
    throw new Error(`Unexpected simulated API ${method} ${url}`);
  };
  ctx.baseApi=ctx.api;ctx.timedApi=(_label,...args)=>ctx.api(...args);
  ctx.serverItems=serverItems;ctx.serverEvents=serverEvents;
  ctx.rebuildRows=()=>{
    fields=[];rows=[];
    for(const item of ctx.getDraftItems(1)){
      const id=String(item.id), row=element({'data-event-item-row':id});
      const localFields=[];
      for(const field of ['external_name','external_price','external_quantity','external_days','amount_fact','payment_method','iin_bin']){
        const f=element({'data-item-field':field,'data-item-id':id},String(item[field]??''));localFields.push(f);fields.push(f);
      }
      const cells=new Map();
      row.querySelector=q=>{
        if(q.startsWith('[data-item-field=')){
          const fm=q.match(/data-item-field="([^"]+)"/), im=q.match(/data-item-id="([^"]+)"/);
          return localFields.find(f=>f.attrs['data-item-field']===fm?.[1]&&f.attrs['data-item-id']===im?.[1])||null;
        }
        if(q.startsWith('[data-check-tax-item=')||q.startsWith('[data-unlock-tax-item=')) return null;
        if(!cells.has(q)) cells.set(q,element());return cells.get(q);
      };
      row.querySelectorAll=q=>q.startsWith('[data-item-field]')?localFields.filter(f=>f.attrs['data-item-field']):[];
      row.rawFields=localFields;rows.push(row);
    }
    ctx.fields=fields;ctx.rows=rows;
  };
  ctx.rebuildRows();
  ctx.field=(id,field)=>fields.find(f=>f.attrs['data-item-id']===String(id)&&f.attrs['data-item-field']===field);
  ctx.getItem=id=>ctx.getDraftItems(1).find(x=>String(x.id)===String(id));
  ctx.store=store;ctx.timers=timers;ctx.holder=holder;
  return ctx;
}
function temp(values={}) {return itemRecord('tmp-audit',{is_temp:true,__client_create_token:'audit-token',external_name:'',external_price:0,external_amount:0,amount_fact:null,payment_method:null,...values});}
async function probe(id,title,fn){let watchdog;const result=await Promise.race([fn(),new Promise((_,reject)=>{watchdog=setTimeout(()=>reject(new Error(`Scenario ${id} did not finish`)),5000);})]).finally(()=>clearTimeout(watchdog));results.push({id,title,...result});console.log(JSON.stringify(results.at(-1)));}

module.exports = {context, itemRecord, eventRecord, coordinator, functionSource};
if (require.main === module) (async()=>{
  await probe('M01','typing survives temporary ID materialization',async()=>{
    const c=context([temp({external_name:'Ф'})]);c.attachDraftInputs(1);const field=c.field('tmp-audit','external_name');
    const item=c.getItem('tmp-audit');await c.saveSingleDraftItem(1,item);
    field.value='Фотограф';field.fire('input');
    assert.equal(item.external_name,'Фотограф');assert.equal(field.attrs['data-item-id'],String(item.id));assert.equal(item.is_temp,false);
    return {dom_id:field.attrs['data-item-id'],model_id:item.id,visible:'Фотограф',stored_draft:item.external_name};
  });
  await probe('M02','payment change retains row text',async()=>{
    const c=context([temp({payment_method:'cash'})]);c.attachDraftInputs(1);
    const item=c.getItem('tmp-audit');const name=c.field(item.id,'external_name');const method=c.field(item.id,'payment_method');
    await c.saveSingleDraftItem(1,item);name.value='Новый ведущий';name.fire('input');method.value='card';method.fire('change');
    const shown=c.rendered.items.find(x=>x.item_type==='regular');
    assert.equal(shown.external_name,'Новый ведущий');assert.equal(shown.payment_method,'card');
    return {typed_name:'Новый ведущий',rendered_name:shown.external_name,selected_method:'card',rendered_method:shown.payment_method};
  });
  await probe('M03','older live response is rejected',async()=>{
    const c=context([itemRecord(11)]);c.state.currentManagerEvent.updated_at='2026-10-15T07:05:00';c.state.managerDraftBaseUpdatedAtByEventId['1']='2026-10-15T07:05:00';
    const applied=c.patchOpenManagerEventPayload({event:eventRecord(1,'2026-10-15T07:00:00'),items:[coordinator()],summary:{}});
    assert.equal(applied,false);assert(c.getItem(11));
    return {applied_older_response:applied,remaining_regular_rows:c.getDraftItems(1).filter(x=>x.item_type==='regular').length,revision:c.state.currentManagerEvent.updated_at};
  });
  await probe('M04','BIN control remains addressable after rendering',async()=>{
    const c=context([itemRecord(11,{payment_method:'invoice',iin_bin:'770100000001',iin_bin_locked:true,tax_check_status:'our_vat'})]);
    const html=c.renderInternalEstimate(c.getDraftItems(1),c.state.currentManagerEvent,{});
    const tag=html.match(/<input[^>]*placeholder="12 цифр"[^>]*>/g).find(x=>x.includes('770100000001'));
    assert(tag.includes('disabled'));assert(tag.includes('data-item-id'));assert(tag.includes('data-item-field'));
    const bin=c.field(11,'iin_bin');bin.disabled=true;c.unlockTaxForItem(11);
    assert.equal(c.getItem(11).iin_bin_locked,false);assert.equal(bin.disabled,false);
    return {active_requests:0,model_unlocked:true,visible_input_still_disabled:bin.disabled,rendered_input:tag};
  });
  await probe('M05','BIN unlock is saved',async()=>{
    const c=context([itemRecord(11,{payment_method:'invoice',iin_bin:'770100000001',iin_bin_locked:true,tax_check_status:'our_vat'})]);
    c.unlockTaxForItem(11);await c.flushManagerDraftAutosave(1);
    assert.equal(c.state.managerDraftDirtyByEventId['1'],false);assert(c.stats.api.some(x=>x.method==='PATCH'));assert(c.stats.storageWrites>0);
    return {dirty:c.state.managerDraftDirtyByEventId['1'],api_calls:c.stats.api.length,local_snapshots:c.stats.storageWrites};
  });
  await probe('M06','verified BIN alone does not fix payment method',async()=>{
    const c=context([itemRecord(11,{payment_method:'invoice',iin_bin:'770100000001',iin_bin_locked:true,tax_check_status:'our_vat'})]);const item=c.getItem(11);
    assert.equal(c.activePaymentRequestsForItem(item).length,0);assert.equal(c.itemPaymentMethodLocked(item),false);
    return {active_requests:0,payment_method_locked:c.itemPaymentMethodLocked(item)};
  });
  await probe('M07','KGD reply retains concurrent edits',async()=>{
    const c=context([temp({external_name:'Старое имя',payment_method:'invoice'})]);const item=c.getItem('tmp-audit'),gate=deferred();let sent;
    c.timedApi=async(_label,_url,opt)=>{sent=JSON.parse(opt.body);return gate.promise;};
    const operation=c.createDraftItemAndCheckTax(1,item,'770100000001','audit');
    c.setDraftItemValue(1,'tmp-audit','external_name','Исправленное имя');
    c.setDraftItemValue(1,'tmp-audit','external_price','200000');
    gate.resolve({item:itemRecord(71,{...sent.item,payment_method:'invoice'}),tax:{iin_bin:'770100000001',iin_bin_locked:true,tax_check_status:'our_vat',vat_amount:100,deduction_amount:200}});
    await operation;assert.equal(item.external_name,'Исправленное имя');assert.equal(Number(item.external_price),200000);assert(item.__dirty_after_save);
    return {typed_name:'Исправленное имя',result_name:item.external_name,typed_price:200000,result_price:item.external_price,edit_version:item.__edit_version};
  });
  await probe('M08','saving A cannot replace the open event B',async()=>{
    const c=context();const gate=deferred();c.api=()=>gate.promise;
    const operation=c.saveDraftEvent(1,{force:true});c.state.selectedManagerEventId=2;c.state.currentManagerEvent=eventRecord(2);c.state.managerDraftEventsById['2']=c.state.currentManagerEvent;
    gate.resolve(eventRecord(1,'2026-10-15T07:04:00'));await operation;
    assert.equal(c.state.selectedManagerEventId,2);assert.equal(c.state.currentManagerEvent.id,2);
    return {selected_event:c.state.selectedManagerEventId,global_editor_event:c.state.currentManagerEvent.id};
  });
  await probe('M09','deletion during creation is persisted',async()=>{
    const c=context([temp({external_name:'Удаляемая строка'})]);const item=c.getItem('tmp-audit'),gate=deferred();
    c.api=async(...args)=>{await gate.promise;return c.baseApi(...args);};
    const operation=c.saveSingleDraftItem(1,item);c.deleteDraftItem(1,'tmp-audit');gate.resolve();await operation;
    assert(!c.getItem(item.id));assert(!c.serverItems.has(item.id));assert.equal(c.getDraftDeletedIds(1).length,0);
    return {hidden_locally:true,exists_on_server:c.serverItems.has(item.id),queued_server_deletions:c.getDraftDeletedIds(1)};
  });
  await probe('M10','deletions added during a save remain queued',async()=>{
    const c=context([itemRecord(11),itemRecord(12,{external_name:'Удалить',sort_order:1})]);c.setDraftItemValue(1,11,'external_name','Изменить');
    const gate=deferred();c.api=async(...args)=>{await gate.promise;return c.baseApi(...args);};
    const operation=c.saveDraftItems(1);c.deleteDraftItem(1,12);assert.equal(c.getDraftDeletedIds(1).length,1);gate.resolve();await operation;
    assert.equal(c.getDraftDeletedIds(1).length,1);assert(c.serverItems.has(12));await c.saveDraftItems(1);assert(!c.serverItems.has(12));
    return {exists_on_server:c.serverItems.has(12),deletion_dropped:false,requests:c.stats.api.map(x=>x.method+' '+x.url)};
  });
  await probe('M11','read after a write never joins an older read',async()=>{
    const c=context();vm.runInContext(functionSource('normalizeInflightGetPath'),c);vm.runInContext(functionSource('api'),c);
    c.withCurrentMonthIfNeeded=x=>x;c.adminDashboardMutationAffectsCache=()=>true;c.invalidateAdminDashboardCaches=()=>{};c.invalidateManagerDashboardCaches=()=>{};
    let value='old',getCount=0;const gate=deferred();
    c.fetch=async(_url,opt)=>{if(opt.method==='PATCH'){value='new';return {ok:true,json:async()=>({revision:value})};}
      getCount++;const captured=value;await gate.promise;return {ok:true,json:async()=>({revision:captured})};};
    const older=c.api('/events/1?_=1');await c.api('/events/1',{method:'PATCH',body:'{}'});
    const fresh=c.api('/events/1?_=2');gate.resolve();const [a,b]=await Promise.all([older,fresh]);
    assert.equal(getCount,2);assert.equal(b.revision,'new');assert.equal(value,'new');
    return {server_revision:value,requested_fresh_revision:b.revision,actual_gets:getCount};
  });
  await probe('M12','one row save skips unchanged header write',async()=>{
    const c=context([itemRecord(11)]);c.setDraftItemValue(1,11,'external_name','Новое имя');c.markManagerDraftChanged(1);
    const ok=await c.flushManagerDraftAutosave(1,{silent:true});assert.equal(ok,true);assert.equal(c.stats.api.length,2);
    return {requests:c.stats.api.map(x=>x.method+' '+x.url),writes:c.stats.api.filter(x=>x.method!=='GET').length};
  });
  await probe('M13','quantity-only row is retained in recovery copy',async()=>{
    const c=context([temp()]);c.setDraftItemValue(1,'tmp-audit','external_quantity','7');c.markManagerDraftChanged(1);
    const snapshot=c.snapshotManagerDraftForAutosave(1);assert(snapshot.items.some(x=>x.item_type==='regular'&&x.external_quantity===7));
    return {typed_quantity:7,regular_rows_in_recovery_copy:snapshot.items.filter(x=>x.item_type==='regular').length};
  });
  await probe('M15','explicit zero expense is stored as zero',async()=>{
    const c=context([itemRecord(11,{amount_fact:null})]);const item=c.getItem(11);
    c.setDraftItemValue(1,11,'amount_fact','0');const payload=c.itemPayloadForSave(item);
    assert.equal(item.amount_fact,0);assert.equal(payload.amount_fact,0);
    const before=c.calculateDraftSummaryPreview(c.getDraftItems(1),c.state.currentManagerEvent,{});
    item.amount_fact=0;const intended=c.calculateDraftSummaryPreview(c.getDraftItems(1),c.state.currentManagerEvent,{});
    assert.equal(before.regular_positions_commission,100000);assert.equal(intended.regular_positions_commission,100000);
    return {typed_fact:0,payload_fact:payload.amount_fact,current_commission:before.regular_positions_commission,intended_commission:intended.regular_positions_commission};
  });
  await probe('M16','late detail response cannot replace a new selection',async()=>{
    const c=context(),first=deferred(),second=deferred();
    vm.runInContext(functionSource('renderManagerEventDetailImpl'),c);
    c.refreshManagerMiniCardSelection=()=>{};c.restoreManagerAutosaveSnapshot=()=>false;
    c.cachedManagerEventPayload=()=>null;c.loadManagerEventPayload=id=>Number(id)===1?first.promise:second.promise;
    const openingFirst=c.renderManagerEventDetailImpl(1,{noLoading:true});
    const openingSecond=c.renderManagerEventDetailImpl(2,{noLoading:true});
    second.resolve({event:eventRecord(2),items:[itemRecord(22,{event_id:2})],summary:{},requests:[]});await openingSecond;
    assert.equal(c.state.currentManagerEvent.id,2);
    first.resolve({event:eventRecord(1),items:[itemRecord(11)],summary:{},requests:[]});await openingFirst;
    assert.equal(c.state.selectedManagerEventId,2);assert.equal(c.state.currentManagerEvent.id,2);assert.equal(c.holder.dataset.loadedEventId,'2');
    return {selected_event:c.state.selectedManagerEventId,rendered_event:c.holder.dataset.loadedEventId};
  });
  await probe('M17','replayed create preserves edits and patches the existing row',async()=>{
    const c=context([temp({external_name:'Новое имя'})]),item=c.getItem('tmp-audit');
    c.serverItems.set(777,itemRecord(777,{external_name:'Старое имя'}));
    c.api=async(url,opt={})=>opt.method==='POST'&&url.endsWith('/items')
      ? {...clone(c.serverItems.get(777)),creation_replayed:true}:c.baseApi(url,opt);
    await c.saveSingleDraftItem(1,item);
    assert.equal(item.id,777);assert.equal(item.external_name,'Новое имя');
    assert.equal(c.serverItems.get(777).external_name,'Новое имя');
    assert(c.stats.api.some(x=>x.url==='/event-items/777'&&x.method==='PATCH'));
    return {existing_id:item.id,stored_name:c.serverItems.get(777).external_name};
  });
  await probe('M18','failed cleanup of a deleted new row is retried',async()=>{
    const c=context([temp({external_name:'Удаляемая строка'})]),item=c.getItem('tmp-audit'),gate=deferred();
    c.api=async(url,opt={})=>{if(url.endsWith('/items')&&opt.method==='POST')await gate.promise;
      if(url.endsWith('/items/bulk-delete'))throw new Error('Temporary disconnect');return c.baseApi(url,opt);};
    const operation=c.saveSingleDraftItem(1,item);c.deleteDraftItem(1,'tmp-audit');gate.resolve();
    await assert.rejects(operation,/Temporary disconnect/);assert(c.getDraftDeletedIds(1).includes(item.id));
    c.api=c.baseApi;await c.saveDraftItems(1);assert(!c.serverItems.has(item.id));
    assert.equal(c.getDraftDeletedIds(1).length,0);
    return {deleted_on_retry:true};
  });
  await probe('M19','reply from an earlier login cannot enter the new session',async()=>{
    const c=context(),gate=deferred();vm.runInContext(functionSource('normalizeInflightGetPath'),c);vm.runInContext(functionSource('api'),c);
    c.withCurrentMonthIfNeeded=x=>x;c.fetch=async()=>({ok:false,status:401,json:async()=>{await gate.promise;return {detail:'Old session'};}});
    const operation=c.api('/auth/me');c.state.token='new-user-token';gate.resolve();
    await assert.rejects(operation,error=>error.code==='SESSION_CHANGED');return {stale_session_rejected:true};
  });
  await probe('M20','a burst of numeric input calculates once in the next frame',async()=>{
    const c=context();c.attachDraftInputs(1);const field=c.field(11,'amount_fact');let calculations=0;
    const original=c.calculateDraftSummaryPreview;c.calculateDraftSummaryPreview=(...args)=>{calculations++;return original(...args);};
    for(const value of ['100','200','300']){field.value=value;field.fire('input');}
    assert.equal(calculations,0);assert.equal(c.stats.rafCallbacks.length,1);
    c.stats.rafCallbacks.shift()();assert.equal(calculations,1);assert.equal(c.getItem(11).amount_fact,300);
    return {input_events:3,summary_calculations:calculations};
  });
  await probe('M21','file uploads share session protection and a response-body timeout',async()=>{
    const c=context();c.FormData=FormData;
    for(const name of ['normalizeInflightGetPath','api','apiForm'])vm.runInContext(functionSource(name),c);
    c.withCurrentMonthIfNeeded=x=>x;c.adminDashboardMutationAffectsCache=()=>false;
    const form=new FormData();form.append('receipt','isolated');let seen;
    c.fetch=async(_url,opt)=>{seen=opt;return {ok:true,json:async()=>({ok:true})};};
    await c.apiForm('/receipt',form);
    assert.equal(seen.body,form);assert(!('Content-Type' in seen.headers));
    c.fetch=async(_url,opt)=>({ok:true,json:()=>new Promise((_,reject)=>opt.signal.addEventListener('abort',()=>reject(Object.assign(new Error('abort'),{name:'AbortError'}))))});
    await assert.rejects(c.apiForm('/receipt',form,{timeoutMs:10}),/не ответил вовремя/);
    return {multipart_boundary_left_to_browser:true,response_body_timeout:true};
  });
  const performanceRows=[];
  for(const count of [20,100,300]){
    const items=Array.from({length:count},(_,i)=>itemRecord(1000+i,{external_name:`Строка ${i}`,sort_order:i}));
    const c=context(items);
    for(const name of ['calculateDraftSummaryPreview','getDraftItems','sanitizeDraftItems','updateCurrentManagerMiniCardLive']){
      const original=c[name];c[name]=function(...args){c.stats.calls[name]=(c.stats.calls[name]||0)+1;const result=original(...args);
        if(name==='getDraftItems') Object.defineProperty(result,'find',{configurable:true,value:function(predicate,thisArg){return Array.prototype.find.call(this,(v,i,a)=>{c.stats.findComparisons++;return predicate.call(thisArg,v,i,a);});}});
        return result;};
    }
    c.attachDraftInputs(1);const field=c.field(1000+count-1,'external_name');const samples=[];let counts;
    for(let i=0;i<8;i++){
      c.stats.calls={};c.stats.storageWrites=0;c.stats.storageBytes=0;c.stats.raf=0;c.stats.findComparisons=0;c.stats.domQueries=0;c.stats.htmlWrites=0;
      field.value=`Новая строка ${i}`;const started=performance.now();field.fire('input');samples.push(performance.now()-started);
      counts={...c.stats.calls,find_comparisons:c.stats.findComparisons,local_storage_writes:c.stats.storageWrites,snapshot_bytes:c.stats.storageBytes,raf_scheduled:c.stats.raf,document_queries:c.stats.domQueries,html_blocks_replaced:c.stats.htmlWrites};
    }
    samples.sort((a,b)=>a-b);performanceRows.push({regular_rows:count,...counts,node_cpu_median_ms:+samples[4].toFixed(2),node_cpu_max_ms:+samples.at(-1).toFixed(2)});
  }
  assert(performanceRows.every(x=>!x.calculateDraftSummaryPreview && x.local_storage_writes===0 && x.find_comparisons<=4*x.regular_rows));
  console.log(JSON.stringify({id:'M14',title:'input work amplification, simulated DOM; no layout/network',measurements:performanceRows}));
  console.log(JSON.stringify({summary:{passed:results.length,performance_cases:performanceRows.length,source_version:'0.6.8',production_access:false,browser_rendering:false}}));
})().catch(error=>{console.error(error.stack);process.exitCode=1;});
