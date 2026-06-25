from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.legacy_events_2026_importer import dry_run_legacy_events_2026_xlsx


router = APIRouter(tags=["legacy_events_2026"])
PAGE_VERSION = "0.5.7"


def require_migration_token(token: str | None):
    expected = get_settings().LEGACY_MIGRATION_TOKEN
    if not expected:
        raise HTTPException(status_code=403, detail="LEGACY_MIGRATION_TOKEN is not set")
    if not token or token != expected:
        raise HTTPException(status_code=403, detail="Invalid migration token")


@router.get("/legacy-events-2026", response_class=HTMLResponse)
def legacy_events_2026_page():
    return HTMLResponse(
        f"""
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contrast legacy events 2026 dry-run</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f7f8f5;color:#151515;margin:0;padding:24px}}
    .card{{max-width:1180px;margin:24px auto;background:#fff;border:1px solid #e2e7dd;border-radius:24px;padding:24px;box-shadow:0 18px 48px rgba(20,30,18,.08)}}
    h1{{margin:0 0 8px;font-size:26px}} h2{{margin:24px 0 10px;font-size:18px}}
    label{{display:block;font-weight:900;margin-top:16px}} input{{width:100%;box-sizing:border-box;margin-top:8px;padding:12px;border:1px solid #dce4d5;border-radius:14px;font-size:15px}}
    button{{margin-top:18px;border:0;border-radius:14px;padding:12px 16px;font-weight:900;cursor:pointer;background:#8DFF00;color:#111}} button:disabled{{opacity:.55;cursor:not-allowed}}
    .muted{{color:#687066}} .warn{{background:#fff2cc;padding:10px;border-radius:12px}} .ok{{background:#eaffd1;padding:10px;border-radius:12px}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:14px 0}}
    .metric{{background:#f3f6ee;border:1px solid #e2e7dd;border-radius:16px;padding:12px}} .metric b{{display:block;font-size:18px;margin-top:4px}}
    table{{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}} th,td{{border-bottom:1px solid #e7ecdf;padding:8px;text-align:left;vertical-align:top}} th{{background:#f3f6ee;position:sticky;top:0;z-index:1}}
    .table-wrap{{max-height:540px;overflow:auto;border:1px solid #e2e7dd;border-radius:16px}} .right{{text-align:right;white-space:nowrap}} .bad{{color:#991b1b;font-weight:900}}
    pre{{white-space:pre-wrap;background:#111;color:#eaffd1;padding:14px;border-radius:14px;overflow:auto;max-height:360px}}
  </style>
</head>
<body>
  <div class="card">
    <h1>Dry-run импорта мероприятий 2026</h1>
    <p class="muted"><b>Страница v{PAGE_VERSION}</b>. Читает только листы Январь–Апрель 2026. Базу не меняет.</p>
    <p class="warn">Оплаты, заявки и Telegram не импортируются. Все будущие исторические мероприятия будут готовиться под менеджера <b>Тест</b>.</p>
    <label>LEGACY_MIGRATION_TOKEN</label>
    <input id="token" type="password" placeholder="token">
    <label>Менеджер для будущего импорта</label>
    <input id="manager" value="Тест">
    <label>XLSX файл старого отчёта</label>
    <input id="file" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
    <button id="dryBtn">Запустить dry-run</button>
    <div id="out"></div>
  </div>
<script>
(function(){{
  const $ = id => document.getElementById(id);
  const fmt = n => new Intl.NumberFormat('ru-RU', {{ maximumFractionDigits: 0 }}).format(Number(n || 0));
  function metric(label, value){{ return `<div class="metric"><span>${{label}}</span><b>${{fmt(value)}}</b></div>`; }}
  function esc(v){{ return String(v ?? '').replace(/[&<>]/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[ch])); }}
  function render(data){{
    if(!data.ok){{ $('out').innerHTML = `<pre>${{esc(JSON.stringify(data,null,2))}}</pre>`; return; }}
    const manager = data.target_manager || {{}};
    let html = `<h2>Итог</h2>`;
    html += manager.found === false ? `<p class="bad">Менеджер "${{esc(manager.requested_name)}}" не найден в базе.</p>` : `<p class="ok">Dry-run: база не менялась. Менеджер: ${{esc(manager.name || manager.requested_name)}}${{manager.found ? ' найден' : ''}}.</p>`;
    html += `<div class="grid">`+
      metric('Мероприятий', data.totals.events)+
      metric('Общий бюджет', data.totals.total_budget)+
      metric('Доход / остаток', data.totals.total_income)+
      metric('Факт расходов', data.totals.fact_sum)+
      metric('Агентские', data.totals.agency_commission)+
      metric('НДС', data.totals.vat_sum)+
      metric('Вычеты', data.totals.deduction_sum)+
      metric('Налоги net', data.totals.taxes_net)+
      metric('ЗП менеджера', data.totals.manager_salary)+
      `</div>`;
    html += `<h2>По месяцам</h2><div class="table-wrap"><table><thead><tr><th>Лист</th><th class="right">Ивенты</th><th class="right">Бюджет</th><th class="right">Доход</th><th class="right">Факт</th><th class="right">Агентские</th><th class="right">Налоги</th><th class="right">ЗП менеджера</th></tr></thead><tbody>`;
    for(const s of data.sheets) html += `<tr><td>${{esc(s.sheet)}}</td><td class="right">${{s.events}}</td><td class="right">${{fmt(s.total_budget)}}</td><td class="right">${{fmt(s.total_income)}}</td><td class="right">${{fmt(s.fact_sum)}}</td><td class="right">${{fmt(s.agency_commission)}}</td><td class="right">${{fmt(s.taxes_net)}}</td><td class="right">${{fmt(s.manager_salary)}}</td></tr>`;
    html += `</tbody></table></div>`;
    html += `<h2>Мероприятия и определённые бюджеты</h2><div class="table-wrap"><table><thead><tr><th>Лист</th><th>Строка</th><th>Дата</th><th>Мероприятие</th><th>Старый менеджер</th><th class="right">Бюджет</th><th class="right">Доход</th><th class="right">Факт</th><th class="right">НДС</th><th class="right">Вычеты</th><th class="right">Агентские</th><th class="right">Налоги</th><th class="right">ЗП менеджера</th><th>Статус</th></tr></thead><tbody>`;
    for(const ev of data.events){{ const b=ev.budget||{{}}; html += `<tr><td>${{esc(ev.sheet)}}</td><td>${{ev.source_row}}</td><td>${{esc(ev.event_date)}}</td><td>${{esc(ev.title)}}</td><td>${{esc(ev.old_manager)}}</td><td class="right">${{fmt(b.total_budget)}}</td><td class="right">${{fmt(b.total_income)}}</td><td class="right">${{fmt(b.fact_sum)}}</td><td class="right">${{fmt(b.vat_sum)}}</td><td class="right">${{fmt(b.deduction_sum)}}</td><td class="right">${{fmt(b.agency_commission)}}</td><td class="right">${{fmt(b.taxes_net)}}</td><td class="right">${{fmt(b.manager_salary)}}</td><td>${{esc(ev.cash_status)}}</td></tr>`; }}
    html += `</tbody></table></div>`;
    if(data.warnings && data.warnings.length) html += `<h2>Предупреждения</h2><pre>${{esc(data.warnings.join('\n'))}}</pre>`;
    html += `<h2>JSON</h2><pre>${{esc(JSON.stringify(data,null,2))}}</pre>`;
    $('out').innerHTML = html;
  }}
  $('dryBtn').addEventListener('click', async function(){{
    const token = $('token').value.trim();
    const manager = $('manager').value.trim() || 'Тест';
    const file = $('file').files && $('file').files[0];
    if(!token || !file) {{ $('out').innerHTML = '<p class="bad">Нужны token и xlsx-файл.</p>'; return; }}
    $('dryBtn').disabled = true; $('out').innerHTML = '<p class="muted">Читаю файл и считаю бюджеты…</p>';
    try{{
      const form = new FormData(); form.append('token', token); form.append('target_manager_name', manager); form.append('file', file);
      const res = await fetch('/api/legacy-events-2026/dry-run', {{ method:'POST', body: form }});
      const data = await res.json(); render(data);
    }}catch(err){{ $('out').innerHTML = `<pre>${{esc(String(err))}}</pre>`; }}
    finally{{ $('dryBtn').disabled = false; }}
  }});
}})();
</script>
</body>
</html>
        """,
        headers={"Cache-Control": "no-store"},
    )


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
