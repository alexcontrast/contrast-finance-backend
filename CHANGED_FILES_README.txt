Contrast Finance v0.40.64

Changed files:
- app/web/app.js
- app/web/index.html

Purpose:
- Optimized manager internal actions: payment request creation, save draft, send to Sasha/review.
- Payment creation no longer saves the whole estimate and no longer reloads the whole dashboard after success.
- Save draft/send review no longer do an extra status PATCH and full dashboard reload.
- Estimate item saving is parallelized for draft/review actions.
- Added frontend PERF logs for manager payment/create and save/review subtasks.
- Web cache-buster updated to v0.40.64.
