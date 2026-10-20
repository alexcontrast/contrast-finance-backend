// Shipped HTML/JS against a DOM and controlled HTTP responses. No live requests.
const {JSDOM,VirtualConsole}=require('jsdom');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||'.');
let passed=0;
async function scenario(method, failure=null) {
 const dom=new JSDOM(fs.readFileSync(path.join(root,'app/web/index.html'),'utf8'),{url:'https://finance.test/',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole:new VirtualConsole()});
 const w=dom.window;
 w.matchMedia=()=>({matches:false,addListener(){},addEventListener(){}});w.ResizeObserver=class{observe(){}disconnect(){}};
 w.alert=()=>{};w.confirm=()=>true;w.__toasts=[];
 const calls=[];
 const event={id:1,manager_id:2,department_id:1,status:'draft',money_status:'waiting_money',client_name:'Test',title:'Test',event_date:'2026-10-20',client_calc_type:'cash',manager_percent:21,updated_at:'2026-10-20T10:00:00'};
 const created={id:77,event_id:1,event_item_id:901,amount_requested:100,payment_method:method,status:'new',money_status:'waiting_money',created_by_user_id:2};
 w.fetch=async(url,opt={})=>{
  calls.push({url,method:opt.method,body:opt.body?JSON.parse(opt.body):null});
  if(url==='/events/1/manager-salary/payment-requests')return failure==='post'?{ok:false,status:400,json:async()=>({detail:{message:'ЗП менеджера равна 0'}})}:{ok:true,json:async()=>created};
  if(url.startsWith('/events/1?'))return failure==='refresh'?{ok:false,status:503,json:async()=>({detail:'Сервер временно недоступен'})}:{ok:true,json:async()=>({...event,updated_at:'2026-10-20T10:01:00'})};
  if(url==='/_structured_error')return {ok:false,status:422,json:async()=>({detail:[{loc:['path','item_id'],msg:'Неверный идентификатор позиции',type:'int_parsing'}]})};
  throw new Error(`Unexpected HTTP ${url}`);
 };
 w.eval(fs.readFileSync(path.join(root,'app/web/app.js'),'utf8')+'\nshowToast=(...args)=>window.__toasts.push(args);window.__test={state,getDraftItems,submitManagerPayment,api,refreshDraftRevisionsAfterExternalMutation};');
 const c=w.__test;
 Object.assign(c.state,{token:'isolated',bootstrap:{user:{id:2,role:'manager',department_id:1}},selectedManagerEventId:1,currentManagerEvent:event,
  currentManagerSummary:{manager_salary:100},managerData:{events:[{...event}]},managerDraftEventsById:{'1':event},managerDraftBaseUpdatedAtByEventId:{'1':event.updated_at},
  managerEventPayloadById:{'1':{event:{...event},items:[],requests:[]}},managerPaymentRequests:[],managerPaymentOperationToken:'one-operation'});
 const content=w.document.getElementById('eventModalContent');
 content.innerHTML=`<select id="paymentItemSelect"><option value="manager_salary">ЗП менеджера</option></select><select id="paymentMethodSelect"><option value="${method}">${method}</option></select><input id="paymentAmountInput" value="100"><input id="paymentCardInput" value="1234567890123456"><input id="paymentSelfEmployedInput" value="Тестовая Фамилия"><textarea id="paymentCommentInput"></textarea><button id="paymentCreateBtn">Создать заявку</button><div id="paymentMessage"></div>`;
 const backdrop=w.document.getElementById('eventModalBackdrop');backdrop.classList.remove('hidden');
 try {
  if(failure==='post') {
   await assert.rejects(c.submitManagerPayment(1),/ЗП менеджера равна 0/);
   assert(!backdrop.classList.contains('hidden'));assert.equal(c.state.managerPaymentRequests.length,0);
   assert.equal(c.state.managerPaymentOperationToken,'one-operation');assert.equal(w.document.getElementById('paymentCreateBtn').disabled,false);
  } else {
   await c.submitManagerPayment(1);
   assert(backdrop.classList.contains('hidden'));assert.equal(c.state.managerPaymentRequests.length,1);
   assert.equal(c.state.managerPaymentRequests[0].id,77);assert.equal(c.state.managerPaymentOperationToken,null);
   assert(w.document.getElementById('paymentCreateBtn').disabled);
   assert(!calls.some(x=>x.url.includes('/event-items/manager_salary')));
   const post=calls.find(x=>x.method==='POST');assert.equal(post.body.payment_method,method);
   if(method==='self_employed')assert.equal(post.body.self_employed_surname,'Тестовая Фамилия');
   if(failure==='refresh')assert(w.__toasts.some(x=>x[0].includes('Повторно отправлять')));
   else assert(w.__toasts.some(x=>x[0]==='Заявка отправлена'));
   await c.submitManagerPayment(1);
   assert.equal(calls.filter(x=>x.method==='POST').length,1,'completed button submitted again');
   await assert.rejects(c.api('/_structured_error'),e=>e.status===422&&e.message==='Неверный идентификатор позиции'&&!e.message.includes('[object Object]'));
  }
  assert.equal(c.state.managerPaymentSubmitting,false);
  passed++;console.log(`PASS ${method} ${failure||'success'}`);
 } finally {w.close();}
}
(async()=>{
 for(const method of ['cash','card','self_employed'])await scenario(method);
 await scenario('self_employed','refresh');
 await scenario('cash','post');
 console.log(JSON.stringify({passed}));
})().catch(e=>{console.error(e);process.exitCode=1;});
