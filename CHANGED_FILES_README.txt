Contrast Finance v0.40.32 changed-only

Fix:
- Admin event edit mode now has an emergency manual override for VAT and deductions.
- Intended for legacy/migration corrections where invoice payment method and BIN/IIN are locked by active payment requests, but imported item VAT/deductions are wrong or zero.
- Does not unlock payment method, BIN/IIN, paid amount, or delete restrictions.

Deploy:
- Upload changed-only over current backend.
- Redeploy web service.
- Hard refresh browser.
