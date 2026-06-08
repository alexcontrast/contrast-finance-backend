from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response


router = APIRouter(tags=["web"])

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


def read_web_file(name: str) -> str:
    path = WEB_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return path.read_text(encoding="utf-8")


@router.get("/", response_class=HTMLResponse)
def web_index():
    return HTMLResponse(read_web_file("index.html"))


@router.get("/web/app.js")
def web_app_js():
    return Response(read_web_file("app.js"), media_type="application/javascript; charset=utf-8")


@router.get("/web/styles.css")
def web_styles_css():
    return Response(read_web_file("styles.css"), media_type="text/css; charset=utf-8")


@router.get("/web/contrast-logo.jpg")
def web_logo():
    path = WEB_DIR / "contrast-logo.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return Response(path.read_bytes(), media_type="image/jpeg")
