Contrast Finance v0.40.31

Fix:
- Admin event edit modal no longer crashes with "holder is not defined".
- Root cause: openAdminEventEditMode called attachCustomerPaymentActions(holder), but holder exists only in installAdminEventModalActions; correct container is eventModalContent/content.
