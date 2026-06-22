# CHANGELOG

## v0.40.70 — Event modal requests table fit

- Fixed admin/department-head event modal requests table width rules.
- Root cause: the table now has 9 columns, but an older high-specificity CSS block in `app.js` still assigned widths as if it had 8 columns. Because of that, the `Деньги` column expanded and the buttons column was squeezed/cut off.
- Rebalanced all 9 columns explicitly.
- Kept request action buttons in one row; removed wrapping behavior.
- Reduced request table padding/button size slightly so buttons fit inside the modal.
- Bumped frontend cache versions to `0.40.70`.
