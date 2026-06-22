# CHANGELOG

## v0.40.57 — Mobile admin overview polish
- Мобильная админка: шапка стала компактной — логотип + «АДМИН», без подписи и текста Contrast Finance 2.0.
- Мобильная админка: месяц и год уложены в одну строку.
- Мобильная админка: скрыт дублирующий заголовок «Админка».
- Мобильная админка: общий план выровнен влево, бейдж количества мероприятий вынесен в правый верхний угол, скрыто слово «Компания» над шкалой.
- Мобильная админка: отделы превращены в горизонтальную карусель свайпом; названия отделов оформлены как компактные заголовки без слова «Отдел».
- Мобильная админка: строки менеджеров сжаты до одной строки данных + шкала заполнения; удалённые менеджеры и кнопки удаления/восстановления скрыты только на мобильной версии.
- Десктопная версия не затрагивалась.

# Changelog

## v0.40.56 — mobile admin compact start

- Added mobile-only admin compact styling under `@media (max-width: 720px)`.
- Login screen and desktop layout are not changed.
- Admin summary cards, toolbar, tabs, filters and text sizes are reduced on mobile.
- Admin events table becomes compact mobile cards with only key information: date, customer, event, manager, status, turnover and income.
- Less important mobile columns are hidden only on mobile: payment type, money status, manager salary and payment request count.

## v0.40.55 — closing month heads performance

- Optimized department-head calculations in the “Закрыть месяц” tab by batching month events, items, shares and users.
