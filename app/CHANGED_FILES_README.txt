v0.5.65 changed files

app/api/routes/manager_bonuses.py
app/api/routes/monthly_closings.py

The two route modules are shipped together so manager bonus payment can recalculate
an already closed month without an import failure.

Deploy over v0.5.64. No new migration is required; 0013_manager_bonus remains current.
