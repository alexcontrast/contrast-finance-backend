from pathlib import Path
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response


router = APIRouter(tags=["web"])

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


@lru_cache(maxsize=4)
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


def versioned_asset_response(content, media_type: str, version: str | None):
    if not version:
        return no_store_response(content, media_type)
    return Response(
        content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
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
def web_app_js(v: str | None = None):
    return versioned_asset_response(read_web_file("app.js"), "application/javascript; charset=utf-8", v)


@router.get("/web/styles.css")
def web_styles_css(v: str | None = None):
    return versioned_asset_response(read_web_file("styles.css"), "text/css; charset=utf-8", v)




@router.get("/web/contrast-logo-transparent.png")
def web_logo_transparent():
    path = WEB_DIR / "contrast-logo-transparent.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return Response(path.read_bytes(), media_type="image/png")


@router.get("/web/contrast-logo.jpg")
def web_logo():
    path = WEB_DIR / "contrast-logo.jpg"
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return Response(path.read_bytes(), media_type="image/jpeg")
