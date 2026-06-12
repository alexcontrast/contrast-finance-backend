from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.services.legacy_importer import import_legacy_data, validate_legacy_data


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
    pre{white-space:pre-wrap;background:#111;color:#eaffd1;padding:14px;border-radius:14px;overflow:auto;max-height:420px}.muted{color:#6c726a}.warn{background:#fff2cc;padding:10px;border-radius:12px}
  </style>
</head>
<body>
  <div class="card">
    <h1>Импорт старого Contrast</h1>
    <p class="muted">1) Сначала запусти сухую проверку. 2) Если ошибок нет — запусти боевой импорт.</p>
    <p class="warn">После успешной миграции лучше сразу удалить переменную <b>LEGACY_MIGRATION_TOKEN</b> или сменить её.</p>
    <label>Migration token</label>
    <input id="token" type="password" placeholder="LEGACY_MIGRATION_TOKEN">
    <label>Файл legacy export JSON</label>
    <input id="file" type="file" accept="application/json,.json">
    <button onclick="runImport(true)">Сухая проверка</button>
    <button class="secondary" onclick="runImport(false)">Импортировать в базу</button>
    <h3>Результат</h3>
    <pre id="out">Жду файл…</pre>
  </div>
<script>
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
async function runImport(dryRun){
  const out = document.getElementById('out');
  const token = document.getElementById('token').value.trim();
  const file = document.getElementById('file').files[0];
  if(!token) return out.textContent = 'Введите token';
  if(!file) return out.textContent = 'Выберите JSON файл';
  out.textContent = dryRun ? 'Быстро проверяю структуру JSON…' : 'Импортирую… не закрывай страницу';
  try{
    const body = await file.text();
    const url = dryRun
      ? `/api/legacy-migration/validate?token=${encodeURIComponent(token)}`
      : `/api/legacy-migration/import?token=${encodeURIComponent(token)}`;
    const res = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body });
    const data = await readJsonResponse(res);
    out.textContent = JSON.stringify(data, null, 2);
  }catch(err){
    out.textContent = String(err && err.message || err);
  }
}
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
