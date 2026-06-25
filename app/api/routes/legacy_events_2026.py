from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.legacy_events_2026_importer import dry_run_legacy_events_2026_xlsx


router = APIRouter(tags=["legacy_events_2026"])
PAGE_VERSION = "0.5.9"


def require_migration_token(token: str | None):
    expected = get_settings().LEGACY_MIGRATION_TOKEN
    if not expected:
        raise HTTPException(status_code=403, detail="LEGACY_MIGRATION_TOKEN is not set")
    if not token or token != expected:
        raise HTTPException(status_code=403, detail="Invalid migration token")


@router.get("/legacy-events-2026", response_class=HTMLResponse)
def legacy_events_2026_page():
    html = r"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contrast legacy events 2026 dry-run</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f7f8f5;color:#151515;margin:0;padding:24px}
    .card{max-width:1180px;margin:24px auto;background:#fff;border:1px solid #e2e7dd;border-radius:24px;padding:24px;box-shadow:0 18px 48px rgba(20,30,18,.08)}
    h1{margin:0 0 8px;font-size:26px} h2{margin:24px 0 10px;font-size:18px}
    label{display:block;font-weight:900;margin-top:16px} input{width:100%;box-sizing:border-box;margin-top:8px;padding:12px;border:1px solid #dce4d5;border-radius:14px;font-size:15px}
    button{margin-top:18px;border:0;border-radius:14px;padding:12px 16px;font-weight:900;cursor:pointer;background:#8DFF00;color:#111} button:disabled{opacity:.55;cursor:not-allowed}
    .muted{color:#687066}.warn{background:#fff2cc;padding:10px;border-radius:12px}.ok{background:#eaffd1;padding:10px;border-radius:12px}.bad{background:#fee2e2;color:#991b1b;font-weight:900;padding:10px;border-radius:12px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:14px 0}
    .metric{background:#f3f6ee;border:1px solid #e2e7dd;border-radius:16px;padding:12px}.metric b{display:block;font-size:18px;margin-top:4px}
    table{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px} th,td{border-bottom:1px solid #e7ecdf;padding:8px;text-align:left;vertical-align:top} th{background:#f3f6ee;position:sticky;top:0;z-index:1}
    .table-wrap{max-height:540px;overflow:auto;border:1px solid #e2e7dd;border-radius:16px}.right{text-align:right;white-space:nowrap}
    pre{white-space:pre-wrap;background:#111;color:#eaffd1;padding:14px;border-radius:14px;overflow:auto;max-height:360px}
    .status{margin-top:14px;padding:10px 12px;border-radius:12px;background:#f3f6ee;border:1px solid #e2e7dd}
    .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  </style>
</head>
<body>
  <div class="card">
    <h1>Dry-run импорта мероприятий 2026</h1>
    <p class="muted"><b>Страница v0.5.9</b>. Читает только листы Январь–Апрель 2026. Базу не меняет.</p>
    <p class="warn">Оплаты, заявки и Telegram не импортируются. Все будущие исторические мероприятия будут готовиться под менеджера <b>Тест</b>.</p>
    <label for="token">LEGACY_MIGRATION_TOKEN</label>
    <input id="token" type="password" autocomplete="off" placeholder="token">
    <label for="manager">Менеджер для будущего импорта</label>
    <input id="manager" value="Тест">
    <label for="fileInput">XLSX файл старого отчёта</label>
    <input id="fileInput" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
    <div id="fileStatus" class="status muted">Файл пока не выбран.</div>
    <div class="row"><button id="dryBtn" type="button">Запустить dry-run</button><button id="clearBtn" type="button">Очистить отчёт</button></div>
    <div id="out" class="status muted">Готов к проверке. Выбери файл и нажми кнопку.</div>
  </div>
<script>
(function(){
  'use strict';
  function byId(id){ return document.getElementById(id); }
  function esc(v){ return String(v == null ? '' : v).replace(/[&<>]/g, function(ch){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[ch]; }); }
  function fmt(n){ return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(Number(n || 0)); }
  function metric(label, value){ return '<div class="metric"><span>'+esc(label)+'</span><b>'+fmt(value)+'</b></div>'; }
  function setStatus(html, kind){ var out=byId('out'); out.className = kind || 'status'; out.innerHTML = html; }
  function selectedFile(){ var input=byId('fileInput'); return input && input.files && input.files.length ? input.files[0] : null; }
  function render(data){
    if(!data || !data.ok){ setStatus('<pre>'+esc(JSON.stringify(data || {error:'empty response'}, null, 2))+'</pre>', 'status bad'); return; }
    var manager = data.target_manager || {};
    var html = '<h2>Итог</h2>';
    html += manager.found === false ? '<p class="bad">Менеджер "'+esc(manager.requested_name)+'" не найден в базе.</p>' : '<p class="ok">Dry-run: база не менялась. Менеджер: '+esc(manager.name || manager.requested_name)+(manager.found ? ' найден' : '')+'.</p>';
    html += '<div class="grid">'+metric('Мероприятий', data.totals.events)+metric('Общий бюджет', data.totals.total_budget)+metric('Доход / остаток', data.totals.total_income)+metric('Факт расходов', data.totals.fact_sum)+metric('Агентские', data.totals.agency_commission)+metric('НДС', data.totals.vat_sum)+metric('Вычеты', data.totals.deduction_sum)+metric('Налоги net', data.totals.taxes_net)+metric('ЗП менеджера', data.totals.manager_salary)+'</div>';
    html += '<h2>По месяцам</h2><div class="table-wrap"><table><thead><tr><th>Лист</th><th class="right">Ивенты</th><th class="right">Бюджет</th><th class="right">Доход</th><th class="right">Факт</th><th class="right">Агентские</th><th class="right">Налоги</th><th class="right">ЗП менеджера</th></tr></thead><tbody>';
    (data.sheets || []).forEach(function(s){ html += '<tr><td>'+esc(s.sheet)+'</td><td class="right">'+s.events+'</td><td class="right">'+fmt(s.total_budget)+'</td><td class="right">'+fmt(s.total_income)+'</td><td class="right">'+fmt(s.fact_sum)+'</td><td class="right">'+fmt(s.agency_commission)+'</td><td class="right">'+fmt(s.taxes_net)+'</td><td class="right">'+fmt(s.manager_salary)+'</td></tr>'; });
    html += '</tbody></table></div>';
    html += '<h2>Мероприятия и определённые бюджеты</h2><div class="table-wrap"><table><thead><tr><th>Лист</th><th>Строка</th><th>Дата</th><th>Мероприятие</th><th>Старый менеджер</th><th class="right">Бюджет</th><th class="right">Доход</th><th class="right">Факт</th><th class="right">НДС</th><th class="right">Вычеты</th><th class="right">Агентские</th><th class="right">Налоги</th><th class="right">ЗП менеджера</th><th>Статус</th></tr></thead><tbody>';
    (data.events || []).forEach(function(ev){ var b=ev.budget||{}; html += '<tr><td>'+esc(ev.sheet)+'</td><td>'+esc(ev.source_row)+'</td><td>'+esc(ev.event_date)+'</td><td>'+esc(ev.title)+'</td><td>'+esc(ev.old_manager)+'</td><td class="right">'+fmt(b.total_budget)+'</td><td class="right">'+fmt(b.total_income)+'</td><td class="right">'+fmt(b.fact_sum)+'</td><td class="right">'+fmt(b.vat_sum)+'</td><td class="right">'+fmt(b.deduction_sum)+'</td><td class="right">'+fmt(b.agency_commission)+'</td><td class="right">'+fmt(b.taxes_net)+'</td><td class="right">'+fmt(b.manager_salary)+'</td><td>'+esc(ev.cash_status)+'</td></tr>'; });
    html += '</tbody></table></div>';
    if(data.warnings && data.warnings.length){ html += '<h2>Предупреждения</h2><pre>'+esc(data.warnings.join('\n'))+'</pre>'; }
    html += '<h2>JSON</h2><pre>'+esc(JSON.stringify(data,null,2))+'</pre>';
    byId('out').className = ''; byId('out').innerHTML = html;
  }
  async function runDryRun(){
    var token = (byId('token').value || '').trim();
    var manager = (byId('manager').value || '').trim() || 'Тест';
    var file = selectedFile();
    if(!token){ setStatus('Не введён LEGACY_MIGRATION_TOKEN.', 'status bad'); return; }
    if(!file){ setStatus('Файл не выбран. Нажми поле XLSX и выбери файл отчёта.', 'status bad'); return; }
    if(!/\.xlsx$/i.test(file.name)){ setStatus('Нужен файл .xlsx, выбран: '+esc(file.name), 'status bad'); return; }
    var btn = byId('dryBtn'); btn.disabled = true;
    setStatus('Файл выбран: <b>'+esc(file.name)+'</b> ('+fmt(file.size)+' байт). Отправляю на backend…', 'status');
    try{
      var form = new FormData();
      form.append('token', token);
      form.append('target_manager_name', manager);
      form.append('file', file, file.name);
      var res = await fetch('/api/legacy-events-2026/dry-run', { method:'POST', body: form, cache:'no-store' });
      var text = await res.text();
      var data;
      try { data = JSON.parse(text); } catch(parseErr) { throw new Error('Backend вернул не JSON: HTTP '+res.status+' '+text.slice(0, 1000)); }
      if(!res.ok){ setStatus('<pre>'+esc(JSON.stringify(data,null,2))+'</pre>', 'status bad'); return; }
      render(data);
    } catch(err){
      setStatus('<pre>'+esc(err && err.stack ? err.stack : String(err))+'</pre>', 'status bad');
    } finally {
      btn.disabled = false;
    }
  }
  byId('fileInput').addEventListener('change', function(){
    var f = selectedFile();
    byId('fileStatus').innerHTML = f ? 'Выбран файл: <b>'+esc(f.name)+'</b>, размер: '+fmt(f.size)+' байт.' : 'Файл пока не выбран.';
  });
  byId('dryBtn').addEventListener('click', function(e){ e.preventDefault(); runDryRun(); });
  byId('clearBtn').addEventListener('click', function(e){ e.preventDefault(); setStatus('Готов к проверке. Выбери файл и нажми кнопку.', 'status muted'); });
})();
</script>
</body>
</html>
"""
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


@router.post("/api/legacy-events-2026/dry-run")
async def legacy_events_2026_dry_run(
    token: str = Form(...),
    target_manager_name: str = Form("Тест"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    require_migration_token(token)
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Нужен .xlsx файл")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Файл пустой")
    return dry_run_legacy_events_2026_xlsx(raw, target_manager_name=target_manager_name, db=db)
