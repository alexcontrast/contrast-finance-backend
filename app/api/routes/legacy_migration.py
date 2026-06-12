from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.legacy_importer import import_legacy_data, import_legacy_data_step, validate_legacy_data


router = APIRouter(tags=["legacy_migration"])


def require_migration_token(token: str | None):
    expected = get_settings().LEGACY_MIGRATION_TOKEN
    if not expected:
        raise HTTPException(status_code=403, detail="LEGACY_MIGRATION_TOKEN is not set")
    if not token or token != expected:
        raise HTTPException(status_code=403, detail="Invalid migration token")


@router.get("/legacy-migration", response_class=HTMLResponse)
def legacy_migration_page():
    return HTMLResponse(
        """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Contrast legacy migration</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f7f8f5;color:#151515;margin:0;padding:24px}
    .card{max-width:760px;margin:40px auto;background:#fff;border:1px solid #e2e7dd;border-radius:24px;padding:24px;box-shadow:0 18px 48px rgba(20,30,18,.08)}
    label{display:block;font-weight:800;margin-top:16px} input{width:100%;box-sizing:border-box;margin-top:8px;padding:12px;border:1px solid #dce4d5;border-radius:14px;font-size:15px}
    button{margin-top:18px;border:0;border-radius:14px;padding:12px 16px;font-weight:900;cursor:pointer;background:#151515;color:#fff} button.secondary{background:#8DFF00;color:#111;margin-left:8px}
    button:disabled{opacity:.55;cursor:not-allowed}.button-row{display:flex;gap:8px;flex-wrap:wrap}.file-state{margin-top:8px;padding:10px 12px;border-radius:12px;background:#f3f6ee;border:1px solid #e2e7dd;color:#475043;font-weight:800;font-size:13px}.file-state.ready{background:#eaffd1;color:#245c16}.file-state.error{background:#fff5f5;color:#991b1b;border-color:#f4cccc}
    pre{white-space:pre-wrap;background:#111;color:#eaffd1;padding:14px;border-radius:14px;overflow:auto;max-height:420px}.muted{color:#6c726a}.warn{background:#fff2cc;padding:10px;border-radius:12px}
  </style>
</head>
<body>
  <div class="card">
    <h1>Импорт старого Contrast</h1>
    <p class="muted">1) Сначала запусти сухую проверку. 2) Если ошибок нет — запусти боевой импорт.</p>
    <p class="warn">После успешной миграции лучше сразу удалить переменную <b>LEGACY_MIGRATION_TOKEN</b> или сменить её.</p>
    <label for="token">Migration token</label>
    <input id="token" type="password" placeholder="LEGACY_MIGRATION_TOKEN" autocomplete="off">
    <label for="file">Файл legacy export JSON</label>
    <input id="file" type="file" accept="application/json,.json">
    <div id="fileState" class="file-state">Файл ещё не выбран</div>
    <div class="button-row">
      <button id="dryRunBtn" type="button">Сухая проверка</button>
      <button id="importBtn" class="secondary" type="button">Импортировать в базу</button>
    </div>
    <h3>Результат</h3>
    <pre id="out">Жду файл…</pre>
  </div>
<script>
(function(){
  const $ = (id) => document.getElementById(id);
  const state = { body: null, fileName: '', busy: false };

  function setOut(value){ $('out').textContent = value; }
  function setBusy(isBusy){
    state.busy = !!isBusy;
    $('dryRunBtn').disabled = state.busy;
    $('importBtn').disabled = state.busy;
    $('file').disabled = state.busy;
  }
  function updateFileState(message, mode){
    const el = $('fileState');
    el.textContent = message;
    el.className = 'file-state' + (mode ? ' ' + mode : '');
  }
  function appendOut(obj){
    const out = $('out');
    out.textContent += (out.textContent ? '\n' : '') + JSON.stringify(obj, null, 2);
    out.scrollTop = out.scrollHeight;
  }
  async function readJsonResponse(res){
    const text = await res.text();
    let data = null;
    try { data = JSON.parse(text); }
    catch(err) {
      return { ok:false, status:res.status, error:`Backend вернул не JSON: ${text.slice(0, 500)}` };
    }
    if(!res.ok) return { ok:false, status:res.status, error:data.detail || data.error || data };
    return data;
  }
  async function postJson(url, body){
    const res = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body });
    return await readJsonResponse(res);
  }
  async function runStep(body, token, step, offset, limit){
    const url = `/api/legacy-migration/import-step?token=${encodeURIComponent(token)}&step=${encodeURIComponent(step)}&offset=${offset || 0}&limit=${limit || 100}`;
    return await postJson(url, body);
  }
  async function readSelectedFile(force){
    const fileInput = $('file');
    const file = fileInput && fileInput.files && fileInput.files[0];
    if(!file) {
      state.body = null;
      state.fileName = '';
      updateFileState('Файл ещё не выбран', 'error');
      return null;
    }
    if(!force && state.body && state.fileName === file.name) return state.body;
    updateFileState(`Читаю файл: ${file.name}…`, '');
    const body = await file.text();
    try { JSON.parse(body); }
    catch(err) {
      state.body = null;
      updateFileState(`Файл выбран, но это невалидный JSON: ${err.message}`, 'error');
      return null;
    }
    state.body = body;
    state.fileName = file.name;
    updateFileState(`Файл выбран: ${file.name} (${Math.round(file.size / 1024)} KB)`, 'ready');
    return body;
  }
  async function runImport(dryRun){
    if(state.busy) return;
    const token = $('token').value.trim();
    if(!token) { setOut('Введите token'); return; }
    const body = await readSelectedFile(false);
    if(!body) { setOut('Выберите JSON-файл заново'); return; }

    setBusy(true);
    setOut(dryRun ? 'Быстро проверяю структуру JSON…' : 'Запускаю пошаговый импорт… не закрывай страницу');
    try{
      if(dryRun){
        const data = await postJson(`/api/legacy-migration/validate?token=${encodeURIComponent(token)}`, body);
        setOut(JSON.stringify(data, null, 2));
        return;
      }

      setOut('');
      const plan = [
        { step:'core', label:'1/6 пользователи, отделы, цели', limit:1 },
        { step:'events', label:'2/6 мероприятия', limit:20 },
        { step:'shares', label:'3/6 доли/соавторы', limit:1 },
        { step:'items', label:'4/6 позиции', limit:100 },
        { step:'payments', label:'5/6 заявки оплат', limit:50 },
        { step:'final', label:'6/6 финальная проверка', limit:1 },
      ];

      for(const item of plan){
        appendOut({ status:'started', label:item.label });
        let offset = 0;
        while(true){
          const data = await runStep(body, token, item.step, offset, item.limit);
          appendOut(data);
          if(!data.ok) throw new Error(JSON.stringify(data));
          const result = data.result || {};
          if(result.done) break;
          offset = result.next_offset || 0;
        }
      }
      appendOut({ ok:true, status:'completed', note:'Пошаговый импорт завершен. Можно открыть сайт и сверить данные.' });
    }catch(err){
      appendOut({ ok:false, error:String(err && err.message || err) });
    }finally{
      setBusy(false);
    }
  }

  window.addEventListener('DOMContentLoaded', function(){
    $('file').addEventListener('change', function(){ readSelectedFile(true); });
    $('dryRunBtn').addEventListener('click', function(){ runImport(true); });
    $('importBtn').addEventListener('click', function(){ runImport(false); });
  });
})();
</script>
</body>
</html>
        """,
        headers={"Cache-Control": "no-store"},
    )


@router.post("/api/legacy-migration/validate")
async def validate_legacy_migration(
    request: Request,
    token: str | None = Query(None),
):
    require_migration_token(token)
    try:
        data = await request.json()
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {err}")
    try:
        result = validate_legacy_data(data)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Legacy validation failed: {err}")
    return {"ok": result.get("valid", False), "dry_run": True, "result": result}



@router.post("/api/legacy-migration/import-step")
async def import_legacy_migration_step(
    request: Request,
    step: str = Query(...),
    offset: int = Query(0),
    limit: int = Query(100),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    require_migration_token(token)
    try:
        data = await request.json()
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {err}")
    try:
        result = import_legacy_data_step(db, data, step=step, offset=offset, limit=limit)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Legacy step import failed [{step} offset={offset}]: {err}")
    return {"ok": True, "result": result}


@router.post("/api/legacy-migration/import")
async def import_legacy_migration(
    request: Request,
    dry_run: bool = Query(False),
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    require_migration_token(token)
    try:
        data = await request.json()
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {err}")
    try:
        result = import_legacy_data(db, data, dry_run=dry_run)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Legacy import failed: {err}")
    return {"ok": True, "dry_run": dry_run, "result": result}
