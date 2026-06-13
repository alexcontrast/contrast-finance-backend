## v0.40.24

Frontend fix for admin/department-head event modal estimate table colors.

- Removed old global nth-child based estimate-column coloring from injected frontend CSS.
- Estimate column backgrounds are now bound to semantic classes instead of column numbers.
- In admin/department-head event modal:
  - NDS column is blue.
  - Deductions column is purple.
  - Commission and Method columns stay neutral/gray like regular amount columns.
- Added explicit method-col classes to event modal estimate header/body/top rows.
- Frontend cache-bust updated to v0.40.24.


## v0.40.28
- Сортировка менеджеров в обзоре админки и главдепа по выполнению плана от большего к меньшему.
