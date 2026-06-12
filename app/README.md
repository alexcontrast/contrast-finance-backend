# Contrast Finance Backend v0.38.7

Changed-only patch based on v0.38.6.

## Что изменилось

Точечный фикс модалки менеджера «Мои оплаты».

Причина большой ширины: общий стиль карточки мероприятия `#eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode)` имел более высокую CSS-специфичность и продолжал применять ширину `1280px` к модалке «Мои оплаты», хотя на backdrop уже был класс `manager-payments-modal`.

В v0.38.7 общий широкий стиль модалки мероприятия исключает режимы `manager-payments-modal` и `manager-requests-modal-mode`, поэтому для «Мои оплаты» снова работают компактные правила `fit-content` по ширине внутренних карточек.

## Что не менялось

- Backend-логика не менялась.
- База данных не менялась.
- Миграций нет.
