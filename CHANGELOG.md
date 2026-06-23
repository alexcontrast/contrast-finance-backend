# CHANGELOG

## v0.40.82 — Event modal customer payment polish

- Desktop event modal metric cards are more compact vertically.
- Manager percent metric label is aligned with the other metric headers.
- Customer payment block now works as an inline editor:
  - enter amount and press ✓;
  - saved amount becomes a grey fixed field;
  - ✓ changes to ✎;
  - ✎ reopens editing;
  - remaining amount stays visible below.
- Customer payment update is now a local modal patch, without reopening/reloading the whole event modal.
- Added button loading state while customer payment is being saved.
- Added backend PATCH endpoint for setting absolute customer paid amount on an event.

## v0.40.81 — Mobile closing expense rows

- Compact mobile expense rows in “Закрыть месяц”.
- Short division labels in the mobile dropdown.
