# Contrast Finance Backend v0.40.110

Patch for two issues:

1. Admin modal customer payment amount now refreshes immediately after saving.
2. Manager percent is protected from manager-side event saves/status changes, so admin overrides are not reset by draft/review transitions.

Deploy as usual by replacing the app files and redeploying the backend/web service.
