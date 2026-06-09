Contrast Finance Backend v0.35.16 — changed files only

Исправление налогов по Упрощенке.

Проблема:
- налог 5% считался от базы до надбавки `Банк+налоги`
- должно быть: 5% от оборота

Теперь для Упрощенки:

    оборот = позиции + агентская комиссия + банк/налоги

    расход по налогам = оборот * 5% - вычеты

Backend:
- для `client_calc_type == "simplified"` internal_tax_amount считается от turnover_with_vat
- tax_base_amount для Упрощенки теперь тоже отдаёт оборот
- taxes_net по-прежнему = taxes_total - deductions_total

Frontend:
- онлайн-preview во внутренней смете считает налог Упрощенки от оборота
- онлайн-preview показывает налог с учетом вычетов

index.html подключает app.js/styles.css с ?v=0.35.16

Миграций нет.
