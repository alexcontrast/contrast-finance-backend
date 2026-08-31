v0.5.94 changed files (apply directly over v0.5-2.93)

alembic/versions/0021_avr_signed_ddc.py
app/api/routes/act_signing.py
app/api/routes/self_employed_accounting.py
app/core/config.py
app/models/self_employed_accounting.py
app/schemas/self_employed_accounting.py
app/services/sigex_signing.py
app/web/app.js
app/web/index.html
app/web/sign_avr.html
app/web/styles.css
CHANGELOG.md
README.md

Permanent SIGEX DDC after two signatures, stored in PostgreSQL and served instead of the unsigned-looking source PDF.
