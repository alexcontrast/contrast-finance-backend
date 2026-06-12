# Contrast Finance Backend v0.38.9

Changed files only.

Hotfix: строгая привязка вкладок входа к ролям.

- вкладка «Вход» пропускает только пользователей с ролью `manager`;
- вкладка «Админ» пропускает только пользователей с ролью `admin`;
- вкладка «Глав Деп» пропускает только пользователей с ролью `department_head`;
- пользователь с правильным PIN, но выбранной не своей вкладкой, получает отказ авторизации;
- бизнес-логика, БД, миграции и frontend-вёрстка не менялись.

Copy files from this archive over the Railway/GitHub project root and deploy.
