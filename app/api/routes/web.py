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


def no_store_response(content, media_type: str):
    return Response(
        content,
        media_type=media_type,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/", response_class=HTMLResponse)
def web_index():
    return HTMLResponse(
        read_web_file("index.html"),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/web/app.js")
def web_app_js():
    return no_store_response(read_web_file("app.js"), "application/javascript; charset=utf-8")


@router.get("/web/styles.css")
def web_styles_css():
    return no_store_response(read_web_file("styles.css"), "text/css; charset=utf-8")


@router.get("/web/contrast-logo.jpg")
def web_logo():
    path = WEB_DIR / "contrast-logo.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return Response(path.read_bytes(), media_type="image/jpeg")
