# CHANGELOG

## v0.40.96 — Department head mobile request cards exact fix
- Rebuilt mobile department-head request cards as a separate card list instead of trying to restyle the desktop table.
- Removed the empty gaps between customer, payment details, amount, and manager in department-head mobile request cards.
- Restored `method / details` formatting for mobile request cards, e.g. `По счету / ОУР без НДС`, `На карту / card`, `Самозанятый / surname`.
- Restored department-head mobile event status/money badges so row/card fill no longer bleeds into badges.
- Removed the negative progress offset in the department-head overview card so target text no longer sticks to the progress bar.
