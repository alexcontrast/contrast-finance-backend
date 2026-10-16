"""Process-isolated production startup boundaries; no external services."""
import os
import subprocess
import sys
import pytest


def run(code, secret=None):
    env=dict(os.environ, ENVIRONMENT="production", RAILWAY_ENVIRONMENT_ID="isolated-test", DATABASE_URL="", GOOGLE_SHEETS_DAILY_EXPORT_ENABLED="false", PYTHONDONTWRITEBYTECODE="1")
    env.pop("JWT_SECRET_KEY",None)
    if secret is not None: env["JWT_SECRET_KEY"]=secret
    return subprocess.run([sys.executable,"-c",code],env=env,capture_output=True,text=True,timeout=20)


def test_bot_import_does_not_require_website_jwt():
    result=run("import app.telegram_bot.main; print('BOT_IMPORT_OK')")
    assert result.returncode==0,result.stderr
    assert "BOT_IMPORT_OK" in result.stdout


@pytest.mark.parametrize("secret",[None,"short","dev-change-me"])
def test_web_still_rejects_missing_or_weak_production_key(secret):
    result=run("import app.main",secret)
    assert result.returncode!=0
    assert "Set JWT_SECRET_KEY" in result.stderr


def test_web_import_accepts_private_production_key():
    result=run("import app.main; print('WEB_IMPORT_OK')","isolated-test-secret-only-1234567890123456")
    assert result.returncode==0,result.stderr
    assert "WEB_IMPORT_OK" in result.stdout


@pytest.mark.parametrize("code",[
    "from app.services.auth import decode_access_token; decode_access_token('invalid')",
    "from app.services.auth import create_access_token; create_access_token(None)",
])
def test_auth_functions_cannot_bypass_secret_validation(code):
    result=run(code)
    assert result.returncode!=0
    assert "Set JWT_SECRET_KEY" in result.stderr
