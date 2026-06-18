Contrast Finance v0.40.78

Admin refund fix:
- Archive request button "Вернуть" now uses POST /payment-requests/{id}/refund.
- Paid requests are not cancellable through the regular status endpoint, but admin can refund them through the dedicated endpoint.
- Refund sets payment status to rejected/cancelled state, money status to cancelled, recalculates item paid_amount, and syncs Telegram cards.
