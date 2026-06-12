Contrast Finance backend v0.40.22 changed-only

Fix:
- Admin event edit mode: deleting or adding an estimate row now rerenders the admin modal content itself.
- Before this fix, the shared editor handler called renderManagerEventDetail(), which only rerenders the manager workspace (#managerEventDetail). In admin modal there is no such holder, so the draft state changed but the visible row stayed in the modal.

Deploy:
- Upload changed-only to Railway web service.
- Redeploy web service.
- Hard refresh browser cache.
