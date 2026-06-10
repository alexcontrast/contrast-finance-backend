
function injectManagerUxStyles() {
  if (document.getElementById("managerUxStyles")) return;
  const style = document.createElement("style");
  style.id = "managerUxStyles";
  style.textContent = `
    .icon-btn.is-loading {
      opacity: .75;
      cursor: progress;
    }

    /* Миникарточки: базово все серые */
    .manager-mini-card {
      background: rgba(115, 120, 130, .10) !important;
      border-color: rgba(115, 120, 130, .26) !important;
      box-shadow: none !important;
      transition: background .15s ease, border-color .15s ease, box-shadow .15s ease, transform .15s ease;
    }

    /* Открытая миникарточка: только зелёная обводка + свечение.
       Фон не трогаем, чтобы цвет статуса оставался прежним. */
    .manager-mini-card.is-open {
      border-color: rgba(80, 210, 40, .90) !important;
      box-shadow:
        0 0 0 2px rgba(80, 210, 40, .30) inset,
        0 8px 28px rgba(80, 210, 40, .18) !important;
    }

    /* Статусы на миникарточках и в карточке */
    .status,
    .status-badge,
    .manager-mini-card em {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      border-radius: 999px;
      padding: 6px 10px;
      font-style: normal;
      font-weight: 800;
      font-size: 13px;
      line-height: 1;
      border: 1px solid transparent;
    }

    .status-tone-draft,
    .status.draft,
    .status.revision,
    .status-badge.status-tone-draft {
      background: rgba(115, 120, 130, .14) !important;
      border-color: rgba(115, 120, 130, .28) !important;
      color: #6b7280 !important;
    }

    .status-tone-review,
    .status.review,
    .status-badge.status-tone-review {
      background: rgba(255, 193, 7, .22) !important;
      border-color: rgba(255, 193, 7, .48) !important;
      color: #8a5a00 !important;
    }

    .status-tone-accepted,
    .status.accepted,
    .status.approved,
    .status.completed,
    .status.done,
    .status.archive,
    .status.archived,
    .status-badge.status-tone-accepted {
      background: rgba(50, 168, 82, .16) !important;
      border-color: rgba(50, 168, 82, .42) !important;
      color: #1f7a35 !important;
    }

    .manager-event-card.is-readonly {
      background: rgba(115, 120, 130, .045);
    }

    .manager-event-card.is-readonly .manager-event-fields,
    .manager-event-card.is-readonly .estimate-table,
    .manager-event-card.is-readonly .manager-summary-grid-six {
      filter: grayscale(.35);
      opacity: .72;
    }

    .manager-event-card.is-readonly input,
    .manager-event-card.is-readonly select,
    .manager-event-card.is-readonly textarea {
      background: rgba(115, 120, 130, .10) !important;
      color: rgba(30, 35, 42, .62) !important;
      border-color: rgba(115, 120, 130, .25) !important;
      cursor: not-allowed !important;
    }

    .readonly-banner {
      margin: 12px 0 0;
      padding: 10px 12px;
      border: 1px solid rgba(50, 168, 82, .35);
      background: rgba(50, 168, 82, .10);
      color: #256b31;
      border-radius: 12px;
      font-size: 13px;
      font-weight: 700;
    }

    .danger-btn,
    button.danger-btn {
      border: 1px solid rgba(180, 35, 24, .55) !important;
      background: rgba(180, 35, 24, .10) !important;
      color: #b42318 !important;
      border-radius: 10px;
      padding: 9px 12px;
      font-weight: 800;
      cursor: pointer;
    }

    .danger-btn:hover,
    button.danger-btn:hover {
      background: rgba(180, 35, 24, .18) !important;
    }

    .danger-btn:disabled,
    button.danger-btn:disabled {
      opacity: .45 !important;
      cursor: not-allowed !important;
    }

    .manager-card-bottom-actions button:disabled,
    .manager-card-bottom-actions .disabled-action {
      background: rgba(115, 120, 130, .22) !important;
      border-color: rgba(115, 120, 130, .28) !important;
      color: rgba(30, 35, 42, .45) !important;
      cursor: not-allowed !important;
      box-shadow: none !important;
      opacity: .85 !important;
    }

    .mini-pill-green {
      background: rgba(50, 168, 82, .14) !important;
      color: #1f7a35 !important;
      border-color: rgba(50, 168, 82, .30) !important;
    }

    .auth-card {
      width: min(560px, calc(100vw - 32px));
      margin: 12vh auto 0;
      padding: 34px 34px 40px;
      border-radius: 24px;
      text-align: center;
      box-shadow: 0 30px 90px rgba(20, 25, 18, .14);
    }

    .auth-logo {
      width: 230px;
      max-width: 70%;
      height: auto;
      display: block;
      margin: 0 auto 18px;
      object-fit: contain;
    }

    .auth-eyebrow {
      color: #39c600;
      text-transform: uppercase;
      letter-spacing: .34em;
      font-size: 13px;
      font-weight: 900;
      margin-bottom: 12px;
    }

    .auth-title {
      font-size: 28px;
      line-height: 1.12;
      margin: 0 0 24px;
      font-weight: 900;
      letter-spacing: -.04em;
    }

    .auth-subtitle {
      font-size: 28px;
      line-height: 1.12;
      margin: 0 0 22px;
      font-weight: 900;
      letter-spacing: -.04em;
    }

    .auth-tabs {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 6px;
      background: rgba(115, 120, 105, .11);
      border: 1px solid rgba(115, 120, 105, .18);
      border-radius: 16px;
      padding: 6px;
      margin: 0 0 20px;
    }

    .auth-tab {
      border: 0;
      background: transparent;
      border-radius: 12px;
      padding: 12px 10px;
      font-weight: 900;
      cursor: pointer;
      color: rgba(25, 30, 24, .72);
    }

    .auth-tab.active {
      background: #5cff00;
      color: #101510;
    }

    #loginScreen label {
      text-align: left;
      display: block;
      font-weight: 900;
      margin-top: 14px;
    }

    #loginScreen input {
      margin-top: 8px;
      width: 100%;
    }

    #loginBtn.is-loading,
    #loginBtn:disabled {
      opacity: .75;
      cursor: progress;
    }

    .manager-action-list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .manager-action-choice {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      width: 100%;
      padding: 14px 16px;
      border: 1px solid rgba(80, 90, 70, .18);
      border-radius: 14px;
      background: rgba(255, 255, 255, .78);
      color: inherit;
      text-align: left;
      cursor: pointer;
    }

    .manager-action-choice:hover {
      border-color: rgba(80, 210, 40, .55);
      box-shadow: 0 8px 22px rgba(80, 210, 40, .12);
      transform: translateY(-1px);
    }

    .manager-action-choice strong {
      font-weight: 900;
    }

    .manager-action-choice span {
      color: rgba(30, 35, 25, .58);
      font-size: 13px;
      font-weight: 700;
    }

    .inline-actions {
      position: relative;
    }

    .manager-action-dropdown {
      position: absolute;
      top: calc(100% + 10px);
      right: 72px;
      z-index: 80;
      width: min(360px, calc(100vw - 40px));
      max-height: 420px;
      overflow: auto;
      padding: 10px;
      border-radius: 18px;
      border: 1px solid rgba(80, 210, 40, .32);
      background: rgba(255, 255, 255, .96);
      box-shadow: 0 18px 50px rgba(20, 25, 20, .18);
      backdrop-filter: blur(10px);
    }

    .manager-action-dropdown-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 4px 4px 10px;
      color: #171717;
    }

    .manager-action-dropdown-list {
      display: grid;
      gap: 8px;
    }

    .manager-action-choice {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 12px 14px;
      border: 1px solid rgba(80, 90, 70, .16);
      border-radius: 14px;
      background: rgba(250, 252, 248, .95);
      color: inherit;
      text-align: left;
      cursor: pointer;
      transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
    }

    .manager-action-choice:hover {
      border-color: rgba(80, 210, 40, .55);
      box-shadow: 0 8px 22px rgba(80, 210, 40, .12);
      transform: translateY(-1px);
    }

    .manager-action-choice-name {
      font-weight: 900;
    }

    .manager-action-choice-department {
      color: rgba(30, 35, 25, .58);
      font-size: 13px;
      font-weight: 800;
    }

    .manager-action-empty {
      padding: 16px;
      color: rgba(30, 35, 25, .62);
      font-weight: 800;
    }

    .inline-actions > button.action-open {
      border-color: rgba(80, 210, 40, .7) !important;
      box-shadow: 0 0 0 2px rgba(80, 210, 40, .16) inset;
    }

    .event-badge-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }

    .coauthor-badge {
      display: inline-flex;
      align-items: center;
      width: fit-content;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 13px;
      line-height: 1;
      font-weight: 900;
      color: #1557c0;
      background: rgba(33, 118, 255, .12);
      border: 1px solid rgba(33, 118, 255, .28);
    }

    .mini-badge-row {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }

    .manager-mini-card .coauthor-badge {
      font-size: 12px;
      padding: 5px 8px;
    }

    /* Mini-card fixed badge layout */
    .manager-mini-card {
      display: grid !important;
      grid-template-rows: auto auto auto auto;
      align-content: start;
      gap: 7px;
      min-width: 0;
      overflow: hidden;
    }

    .manager-mini-card .mini-card-pills {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 6px;
      width: 100%;
      min-width: 0;
      align-items: center;
    }

    .manager-mini-card .mini-pill {
      min-width: 0;
      max-width: 100%;
      width: 100%;
      display: inline-block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      font-size: clamp(10px, 1.05vw, 12px);
      line-height: 1.05;
      padding: 6px 8px;
    }

    .manager-mini-card .mini-pill strong {
      white-space: nowrap;
    }

    .manager-mini-card [data-mini-title],
    .manager-mini-card [data-mini-meta],
    .manager-mini-card [data-mini-calc] {
      min-width: 0;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .manager-mini-card [data-mini-title],
    .manager-mini-card [data-mini-meta],
    .manager-mini-card [data-mini-calc],
    .manager-mini-card .mini-badge-row {
      width: 100%;
    }

    .manager-mini-card [data-mini-title] {
      white-space: nowrap;
    }

    .manager-mini-card [data-mini-meta],
    .manager-mini-card [data-mini-calc] {
      white-space: nowrap;
    }

    .manager-mini-card .mini-badge-row {
      display: grid !important;
      grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr);
      gap: 6px;
      align-items: center;
      min-width: 0;
      margin-top: 2px;
    }

    .manager-mini-card .mini-badge-row .status-badge,
    .manager-mini-card .mini-badge-row .coauthor-badge {
      min-width: 0;
      max-width: 100%;
      width: 100%;
      display: inline-block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      text-align: center;
      font-size: clamp(9px, 1vw, 12px);
      line-height: 1.05;
      padding: 5px 7px;
    }

    .manager-mini-card .mini-badge-row .coauthor-badge:only-child,
    .manager-mini-card .mini-badge-row .status-badge:only-child {
      grid-column: 1 / -1;
      width: fit-content;
      max-width: 100%;
      justify-self: start;
    }

    /* Mini-card badge fitting without ellipsis */
    .manager-mini-card .mini-pill,
    .manager-mini-card .mini-badge-row .status-badge,
    .manager-mini-card .mini-badge-row .coauthor-badge {
      text-overflow: clip !important;
      overflow: hidden !important;
      white-space: nowrap !important;
      transform-origin: left center;
      will-change: transform, font-size;
    }

    .manager-mini-card .mini-card-pills,
    .manager-mini-card .mini-badge-row {
      overflow: visible;
    }

    .manager-mini-card .mini-pill {
      font-size: 12px;
    }

    .manager-mini-card .mini-badge-row .status-badge,
    .manager-mini-card .mini-badge-row .coauthor-badge {
      font-size: 12px;
    }


    .manager-profile-mini {
      display: inline-flex;
      align-items: center;
      max-width: 420px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      color: rgba(30, 35, 25, .62);
      font-size: 13px;
      font-weight: 800;
    }

    .profile-modal-content .form-grid {
      margin-top: 14px;
    }

    .modal-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 16px;
      flex-wrap: wrap;
    }



    .modal-backdrop.pin-modal-mode .modal {
      width: min(430px, calc(100vw - 36px));
      max-width: 430px;
      padding: 22px;
      border-radius: 22px;
    }

    .modal-backdrop.pin-modal-mode .modal-head {
      align-items: center;
      margin-bottom: 10px;
    }

    .modal-backdrop.pin-modal-mode .modal-head .eyebrow {
      font-size: 11px;
    }

    .modal-backdrop.pin-modal-mode .modal-head h2 {
      font-size: 22px;
      margin: 2px 0 0;
    }

    .pin-modal-content {
      max-width: 100%;
    }

    .pin-form-vertical {
      display: grid;
      grid-template-columns: 1fr;
      gap: 12px;
      margin-top: 12px;
    }

    .pin-form-vertical input {
      width: 100%;
    }

    .pin-actions {
      margin-top: 14px;
    }


    #userBadge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      padding: 9px 12px 9px 14px;
    }

    #userBadge.hidden {
      display: none;
    }

    .user-badge-main {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 2px;
      min-width: 0;
      line-height: 1.05;
    }

    .user-badge-line,
    .user-badge-role {
      display: block;
      min-width: 0;
      max-width: 230px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .user-badge-line {
      font-weight: 950;
    }

    .user-badge-role {
      font-size: 13px;
      opacity: .88;
    }

    .user-badge-edit {
      width: 25px;
      height: 25px;
      min-width: 25px;
      border-radius: 999px;
      border: 1px solid rgba(80, 210, 40, .34);
      background: rgba(255, 255, 255, .62);
      color: #245f18;
      font-size: 12px;
      line-height: 1;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0;
    }

    .user-badge-edit:hover {
      border-color: rgba(80, 210, 40, .72);
      box-shadow: 0 0 0 3px rgba(80, 210, 40, .12);
    }


    .modal-backdrop.profile-modal-mode .modal {
      width: min(460px, calc(100vw - 36px));
      max-width: 460px;
      padding: 22px;
      border-radius: 22px;
    }

    .modal-backdrop.profile-modal-mode .modal-head {
      align-items: center;
      margin-bottom: 10px;
    }


    .modal-backdrop.profile-modal-mode .profile-modal-content input,
    .modal-backdrop.profile-modal-mode .profile-modal-content select {
      width: 100%;
    }

    .modal-backdrop.profile-modal-mode .modal-actions {
      margin-top: 14px;
    }


    .modal-backdrop.profile-modal-mode .modal-head .eyebrow {
      display: none;
    }

    .modal-backdrop.profile-modal-mode .modal-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }

    .modal-backdrop.profile-modal-mode .modal-head h2 {
      font-size: 24px;
      line-height: 1.05;
      margin: 0;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content .form-grid {
      margin-top: 0;
    }

    /* Profile modal final compact one-column layout */
    .modal-backdrop.profile-modal-mode .modal {
      width: min(520px, calc(100vw - 32px)) !important;
      max-width: 520px !important;
      padding: 24px !important;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content {
      width: 100% !important;
      max-width: 100% !important;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content .form-grid {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) !important;
      gap: 14px !important;
      width: 100% !important;
      max-width: 100% !important;
      margin-top: 0 !important;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content label {
      display: grid !important;
      grid-template-columns: minmax(0, 1fr) !important;
      gap: 7px !important;
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      font-size: 15px !important;
      line-height: 1.15 !important;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content input,
    .modal-backdrop.profile-modal-mode .profile-modal-content select {
      width: 100% !important;
      max-width: 100% !important;
      min-width: 0 !important;
      box-sizing: border-box !important;
      font-size: 17px !important;
      line-height: 1.2 !important;
      padding: 13px 16px !important;
      height: auto !important;
      min-height: 52px !important;
      overflow: visible !important;
      text-overflow: clip !important;
    }

    .modal-backdrop.profile-modal-mode .profile-modal-content #profilePhoneInput {
      font-size: 16px !important;
      letter-spacing: -0.2px !important;
    }

    .modal-backdrop.profile-modal-mode .modal-actions {
      display: flex !important;
      gap: 10px !important;
      margin-top: 16px !important;
    }

    .modal-backdrop.profile-modal-mode .modal-actions button {
      font-size: 16px !important;
      padding: 13px 18px !important;
    }


    .modal-backdrop.payment-modal-mode .modal {
      width: min(520px, calc(100vw - 32px));
      max-width: 520px;
      padding: 24px;
      border-radius: 22px;
    }

    .modal-backdrop.payment-modal-mode .modal-head .eyebrow {
      display: none;
    }

    .modal-backdrop.payment-modal-mode .modal-head h2 {
      font-size: 24px;
      margin: 0;
    }

    .manager-pay-modal {
      display: grid;
      gap: 14px;
    }

    .manager-pay-modal label {
      display: grid;
      gap: 7px;
      font-size: 14px;
      font-weight: 800;
      color: rgba(30, 35, 25, .72);
    }

    .manager-pay-modal input,
    .manager-pay-modal select {
      width: 100%;
      box-sizing: border-box;
      font-size: 16px;
      padding: 13px 15px;
      min-height: 50px;
    }

    .payment-info-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }

    .payment-info-grid div {
      border: 1px solid rgba(80, 210, 40, .20);
      background: rgba(80, 210, 40, .08);
      border-radius: 14px;
      padding: 9px 10px;
      min-width: 0;
    }

    .payment-info-grid span {
      display: block;
      color: rgba(30, 35, 25, .62);
      font-size: 11px;
      font-weight: 800;
      margin-bottom: 3px;
    }

    .payment-info-grid strong {
      display: block;
      font-size: 13px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .payment-extra-hint {
      color: rgba(30, 35, 25, .62);
      font-size: 12px;
      font-weight: 700;
      margin-top: -6px;
    }

    #paymentMessage {
      color: #8a2a2a;
      font-weight: 800;
    }


    .payment-bin-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
    }

    .payment-bin-row button {
      min-height: 50px;
      white-space: nowrap;
    }

    .payment-bin-row input:disabled {
      background: rgba(80, 210, 40, .08);
      color: #1b1f18;
      opacity: 1;
      cursor: not-allowed;
    }

    .app-toast {
      position: fixed;
      left: 50%;
      bottom: 28px;
      transform: translateX(-50%) translateY(20px);
      z-index: 10000;
      background: rgba(34, 98, 22, .94);
      color: #fff;
      border-radius: 999px;
      padding: 13px 18px;
      font-weight: 900;
      box-shadow: 0 18px 45px rgba(0, 0, 0, .22);
      opacity: 0;
      pointer-events: none;
      transition: opacity .18s ease, transform .18s ease;
    }

    .app-toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }


    #paymentNewPositionNameLabel {
      margin-bottom: 4px;
    }

    .payment-fixed-hint {
      border: 1px solid rgba(80, 210, 40, .22);
      background: rgba(80, 210, 40, .08);
      border-radius: 12px;
      padding: 9px 10px;
      margin-top: 8px;
    }

    #paymentMethodSelect:disabled,
    #paymentSelfEmployedInput:disabled {
      background: rgba(80, 210, 40, .08);
      color: #1b1f18;
      opacity: 1;
      cursor: not-allowed;
    }


    .icon-btn.danger:disabled {
      opacity: .35;
      cursor: not-allowed;
      filter: grayscale(1);
    }


    .payment-check-bin-btn:disabled,
    .payment-check-bin-btn.is-disabled {
      background: rgba(120, 126, 136, .16) !important;
      color: rgba(60, 66, 76, .55) !important;
      border-color: rgba(120, 126, 136, .25) !important;
      box-shadow: none !important;
      cursor: not-allowed !important;
      filter: grayscale(1);
      opacity: .7;
    }


    .manager-event-requests-list {
      display: grid;
      gap: 12px;
    }

    .manager-payment-request-card {
      border: 1px solid rgba(20, 36, 18, .10);
      background: rgba(255, 255, 255, .82);
      border-radius: 16px;
      padding: 14px;
      box-shadow: 0 10px 24px rgba(20, 36, 18, .06);
    }

    .manager-payment-request-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }

    .manager-payment-request-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }

    .manager-payment-request-grid span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 3px;
    }

    .manager-payment-request-grid strong {
      font-size: 14px;
      color: var(--text);
      word-break: break-word;
    }

    .manager-payment-request-actions {
      justify-content: flex-end;
      margin-top: 12px;
    }

    @media (max-width: 640px) {
      .manager-payment-request-grid {
        grid-template-columns: 1fr;
      }
    }


    .compact-payments-modal {
      width: min(100%, 980px);
    }

    .manager-payments-table-head {
      display: grid;
      grid-template-columns: minmax(180px, 1.4fr) 140px 130px 130px 130px;
      gap: 12px;
      align-items: center;
      padding: 0 12px 8px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .manager-event-requests-list.compact {
      display: grid;
      gap: 8px;
    }

    .manager-payment-request-row {
      display: grid;
      grid-template-columns: minmax(180px, 1.4fr) 140px 130px 130px 130px;
      gap: 12px;
      align-items: center;
      min-height: 58px;
      padding: 10px 12px;
      border: 1px solid rgba(20, 36, 18, .10);
      background: rgba(255, 255, 255, .9);
      border-radius: 14px;
      box-shadow: 0 8px 20px rgba(20, 36, 18, .045);
    }

    .manager-payment-request-position {
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 15px;
      font-weight: 900;
      color: var(--text);
    }

    .manager-payment-request-amount {
      font-size: 18px;
      line-height: 1;
      font-weight: 1000;
      color: #111;
      white-space: nowrap;
    }

    .manager-payment-request-method {
      font-size: 14px;
      font-weight: 850;
      color: var(--text);
      white-space: nowrap;
    }

    .manager-payment-request-status .status {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 4px 10px;
      white-space: nowrap;
    }

    .manager-payment-request-action {
      display: flex;
      justify-content: flex-end;
    }

    .manager-request-cancel-btn {
      min-height: 34px;
      padding: 7px 12px;
      border-radius: 12px;
      white-space: nowrap;
    }

    .manager-request-cancel-btn:disabled {
      opacity: .42;
      cursor: not-allowed;
      filter: grayscale(1);
      box-shadow: none !important;
    }

    @media (max-width: 760px) {
      .manager-payments-table-head {
        display: none;
      }

      .manager-payment-request-row {
        grid-template-columns: 1fr auto;
        gap: 8px 12px;
        min-height: auto;
      }

      .manager-payment-request-position {
        grid-column: 1 / -1;
      }

      .manager-payment-request-amount {
        font-size: 17px;
      }

      .manager-payment-request-action {
        justify-content: flex-start;
      }
    }


    .grouped-payments-modal {
      display: grid;
      gap: 14px;
    }

    .manager-payment-position-group {
      border: 1px solid rgba(20, 36, 18, .10);
      background: rgba(246, 250, 242, .72);
      border-radius: 16px;
      padding: 10px;
    }

    .manager-payment-position-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 0 2px 10px;
    }

    .manager-payment-position-title span {
      font-size: 16px;
      font-weight: 1000;
      color: var(--text);
    }

    .manager-payment-position-title em {
      font-style: normal;
      font-size: 12px;
      font-weight: 850;
      color: var(--muted);
      white-space: nowrap;
    }

    .manager-payment-position-group .manager-payments-table-head {
      padding-left: 10px;
      padding-right: 10px;
    }

    .manager-payment-position-group .manager-payment-request-row {
      box-shadow: none;
      background: rgba(255,255,255,.96);
    }


    .compact-grouped-payments {
      gap: 8px !important;
    }

    .manager-payment-position-group.compact {
      padding: 8px 10px !important;
      border-radius: 14px !important;
      background: rgba(246, 250, 242, .58) !important;
    }

    .manager-payment-position-title.compact {
      padding: 0 2px 6px !important;
      margin: 0 !important;
    }

    .manager-payment-position-title.compact span {
      font-size: 15px !important;
      line-height: 1.1 !important;
    }

    .manager-payment-position-title.compact em {
      font-size: 11px !important;
    }

    .manager-payment-request-row.compact {
      grid-template-columns: 120px minmax(110px, .9fr) 120px 110px !important;
      min-height: 42px !important;
      padding: 7px 10px !important;
      border-radius: 12px !important;
      gap: 10px !important;
      box-shadow: none !important;
    }

    .manager-payment-request-row.compact .manager-payment-request-amount {
      font-size: 17px !important;
      font-weight: 1000 !important;
    }

    .manager-payment-request-row.compact .manager-payment-request-method {
      font-size: 13px !important;
      font-weight: 850 !important;
    }

    .manager-payment-request-row.compact .status {
      min-height: 24px !important;
      padding: 3px 9px !important;
      font-size: 12px !important;
    }

    .manager-payment-request-row.compact .manager-request-cancel-btn {
      min-height: 30px !important;
      padding: 5px 10px !important;
      border-radius: 10px !important;
      font-size: 12px !important;
    }

    .manager-payment-position-group.compact .manager-payments-table-head {
      display: none !important;
    }

    @media (max-width: 760px) {
      .manager-payment-request-row.compact {
        grid-template-columns: 1fr auto !important;
      }

      .manager-payment-request-row.compact .manager-payment-request-amount {
        font-size: 16px !important;
      }
    }


    .modal-backdrop.manager-requests-modal-mode .modal {
      max-width: 860px !important;
    }

    .compact-grouped-payments {
      width: fit-content !important;
      min-width: 620px !important;
      max-width: 100% !important;
      margin: 0 auto !important;
    }

    .manager-payment-position-group.compact {
      width: 100% !important;
    }

    .manager-payment-request-row.compact {
      grid-template-columns: 110px 150px 112px 104px !important;
      width: fit-content !important;
      min-width: 560px !important;
      max-width: 100% !important;
      justify-content: start !important;
    }

    .manager-payment-request-row.compact .manager-payment-request-action {
      justify-content: flex-end !important;
    }

    .manager-payment-request-row.compact .manager-payment-request-method {
      min-width: 0 !important;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    @media (max-width: 760px) {
      .modal-backdrop.manager-requests-modal-mode .modal {
        max-width: calc(100vw - 20px) !important;
      }

      .compact-grouped-payments {
        width: 100% !important;
        min-width: 0 !important;
        margin: 0 !important;
      }

      .manager-payment-request-row.compact {
        width: 100% !important;
        min-width: 0 !important;
        grid-template-columns: 1fr auto !important;
      }
    }


    /* v0.35.81: global grey payment badge for status "new" */
    .status.new {
      background: rgba(120, 126, 136, .13) !important;
      color: #636a61 !important;
      border-color: rgba(120, 126, 136, .28) !important;
      box-shadow: none !important;
    }

    /* v0.35.81: narrower "Мои оплаты" modal */
    .modal-backdrop.manager-requests-modal-mode .modal {
      width: fit-content !important;
      max-width: min(720px, calc(100vw - 32px)) !important;
      min-width: 0 !important;
      padding-left: 28px !important;
      padding-right: 28px !important;
    }

    .modal-backdrop.manager-requests-modal-mode .modal-head {
      width: 100% !important;
      min-width: 0 !important;
      display: grid !important;
      grid-template-columns: 1fr auto !important;
      gap: 18px !important;
    }

    .modal-backdrop.manager-requests-modal-mode #eventModalContent {
      width: fit-content !important;
      max-width: 100% !important;
      margin: 0 auto !important;
    }

    .modal-backdrop.manager-requests-modal-mode .compact-grouped-payments {
      width: fit-content !important;
      min-width: 560px !important;
      max-width: 100% !important;
      margin: 0 auto !important;
    }

    .modal-backdrop.manager-requests-modal-mode .manager-payment-request-row.compact {
      grid-template-columns: 100px 135px 104px 100px !important;
      min-width: 510px !important;
      width: 510px !important;
      max-width: 100% !important;
    }

    .modal-backdrop.manager-requests-modal-mode .manager-payment-position-group.compact {
      width: fit-content !important;
      max-width: 100% !important;
    }

    @media (max-width: 760px) {
      .modal-backdrop.manager-requests-modal-mode .modal {
        width: calc(100vw - 20px) !important;
        max-width: calc(100vw - 20px) !important;
        padding-left: 18px !important;
        padding-right: 18px !important;
      }

      .modal-backdrop.manager-requests-modal-mode .compact-grouped-payments {
        width: 100% !important;
        min-width: 0 !important;
      }

      .modal-backdrop.manager-requests-modal-mode .manager-payment-request-row.compact {
        width: 100% !important;
        min-width: 0 !important;
        grid-template-columns: 1fr auto !important;
      }
    }


    /* v0.35.86: global soft loading feedback for buttons */
    button.soft-loading:not(.is-loading) {
      position: relative;
      opacity: .78;
      pointer-events: none;
      transform: translateY(1px);
      transition: opacity .15s ease, transform .15s ease;
    }

    button.soft-loading:not(.is-loading)::after {
      content: "";
      display: inline-block;
      width: 12px;
      height: 12px;
      margin-left: 8px;
      vertical-align: -2px;
      border: 2px solid currentColor;
      border-right-color: transparent;
      border-radius: 50%;
      animation: cfSoftSpin .7s linear infinite;
      opacity: .7;
    }

    button.soft-loading.icon-btn:not(.is-loading)::after {
      margin-left: 0;
      position: absolute;
      right: 4px;
      bottom: 4px;
      width: 8px;
      height: 8px;
      border-width: 1.5px;
    }

    @keyframes cfSoftSpin {
      to { transform: rotate(360deg); }
    }


    /* v0.35.87: no green user badge in admin header */
    body.admin-mode #userBadge,
    #userBadge.admin-hidden {
      display: none !important;
    }


    /* v0.35.89: цельная заливка строк мероприятий в админке */
    .admin-events-table {
      border-collapse: separate;
      border-spacing: 0 7px;
    }

    .admin-events-table tbody tr.admin-event-row {
      overflow: hidden;
    }

    .admin-events-table tbody tr.admin-event-row td {
      border-top: 1px solid transparent;
      border-bottom: 1px solid transparent;
      background-clip: padding-box;
    }

    .admin-events-table tbody tr.admin-event-row td:first-child {
      border-top-left-radius: 14px;
      border-bottom-left-radius: 14px;
    }

    .admin-events-table tbody tr.admin-event-row td:last-child {
      border-top-right-radius: 14px;
      border-bottom-right-radius: 14px;
    }

    .admin-events-table tbody tr.admin-event-row.status-tone-draft td {
      background: rgba(255, 244, 214, .72) !important;
      border-color: rgba(199, 151, 40, .14);
    }

    .admin-events-table tbody tr.admin-event-row.status-tone-review td {
      background: rgba(226, 241, 255, .76) !important;
      border-color: rgba(46, 126, 190, .13);
    }

    .admin-events-table tbody tr.admin-event-row.status-tone-accepted td {
      background: rgba(227, 247, 221, .78) !important;
      border-color: rgba(53, 150, 57, .14);
    }

    .admin-events-table .admin-event-status-badge {
      box-shadow: none !important;
      background: rgba(255, 255, 255, .62) !important;
    }
`;
  document.head.appendChild(style);
}


injectManagerUxStyles();

const state = {
  token: localStorage.getItem("cf_token") || "",
  bootstrap: null,
  month: new Date().toISOString().slice(0, 7),
  paymentStatusFilter: "active",
  paymentSearch: "",
  paymentCustomerFilter: "all",
  paymentManagerFilter: "all",
  eventDepartmentFilter: "all",
  eventManagerFilter: "all",
  eventStatusFilter: "all",
  eventSearch: "",
  activeAdminTab: "overview",
  activeManagerTab: "events",
  selectedManagerEventId: null,
  managerEstimateTab: "external",
  managerDraftItemsByEventId: {},
  managerDraftDeletedByEventId: {},
  managerDraftEventsById: {},
  managerDraftTempSeq: 1,
  adminData: null,
  users: [],
  authMode: "manager",
};

const $ = (id) => document.getElementById(id);


const MONTHS_RU = [
  ["01", "Январь"],
  ["02", "Февраль"],
  ["03", "Март"],
  ["04", "Апрель"],
  ["05", "Май"],
  ["06", "Июнь"],
  ["07", "Июль"],
  ["08", "Август"],
  ["09", "Сентябрь"],
  ["10", "Октябрь"],
  ["11", "Ноябрь"],
  ["12", "Декабрь"],
];

function setupMonthYearSelectors() {
  const monthSelect = $("monthSelect");
  const yearSelect = $("yearSelect");
  if (!monthSelect || !yearSelect) return;

  const [currentYear, currentMonth] = state.month.split("-");

  monthSelect.innerHTML = MONTHS_RU.map(([value, label]) => `
    <option value="${value}" ${value === currentMonth ? "selected" : ""}>${label}</option>
  `).join("");

  const thisYear = new Date().getFullYear();
  const years = [];
  for (let year = thisYear - 1; year <= thisYear + 2; year += 1) years.push(year);

  if (!years.includes(Number(currentYear))) years.push(Number(currentYear));
  years.sort();

  yearSelect.innerHTML = years.map((year) => `
    <option value="${year}" ${String(year) === String(currentYear) ? "selected" : ""}>${year}</option>
  `).join("");
}

function selectedMonthValue() {
  const monthSelect = $("monthSelect");
  const yearSelect = $("yearSelect");

  if (!monthSelect || !yearSelect) return state.month;

  const month = monthSelect.value || state.month.slice(5, 7);
  const year = yearSelect.value || state.month.slice(0, 4);

  return `${year}-${month}`;
}

function attachMonthYearSelectors() {
  const monthSelect = $("monthSelect");
  const yearSelect = $("yearSelect");

  [monthSelect, yearSelect].forEach((select) => {
    if (!select) return;
    select.addEventListener("change", async () => {
      state.month = selectedMonthValue();
      state.paymentCustomerFilter = "all";
      state.paymentManagerFilter = "all";
      const user = state.bootstrap?.user;
      if (user?.role === "manager") {
        clearManagerSelectedEventUi();
      } else {
        clearDashboardForPeriodLoading();
      }
      await withLoading(loadDashboard, "Загружаем кабинет…");
    });
  });
}


function formatMoney(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n);
}


function formatPlainNumber(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(Math.round(n));
}


function formatInputNumber(value) {
  if (value === null || value === undefined || value === "") return "";
  const n = normalizeNumberInput(value);
  if (!Number.isFinite(n)) return "";
  return formatMoney(Math.round(n));
}

function integerInputValue(value, fallback = "") {
  if (value === null || value === undefined || value === "") return fallback;
  const n = normalizeNumberInput(value);
  if (!Number.isFinite(n)) return fallback;
  return String(Math.round(n));
}


function formatDateRu(value) {
  if (!value) return "";
  const parts = String(value).slice(0, 10).split("-");
  if (parts.length !== 3) return value;
  return `${parts[2]}-${parts[1]}-${parts[0]}`;
}

function asNumber(value) {
  return Number(value || 0);
}

function roleLabel(role) {
  return {
    admin: "Админ",
    manager: "Менеджер",
    department_head: "Руководитель отдела",
    accountant: "Бухгалтер",
  }[role] || role;
}

function statusLabel(status) {
  return {
    draft: "Черновик",
    review: "На проверке",
    revision: "На доработке",
    completed: "Завершено",
    cancelled: "Отменено",
    new: "Новая",
    to_pay: "На оплату",
    paid: "Оплачено",
    cash_received: "Деньги в кассе",
    rejected: "Отменено",
    tax_check_needed: "Нужна проверка",
  }[status] || status;
}

function paymentMethodLabel(method) {
  return {
    invoice: "По счету",
    card: "На карту",
    cash: "Налик",
    self_employed: "Самозанятый",
    "По счету": "По счету",
    "На карту": "На карту",
    "Налик": "Налик",
    "Самозанятый": "Самозанятый",
  }[method] || method || "";
}


function calcTypeLabel(type) {
  return {
    ip_contrast_event: "ИП Contrast Event",
    our_no_vat: "ОУР без НДС",
    simplified: "Упрощенка",
    cash: "Нал",
  }[type] || type || "";
}


function customerPaymentLabel(type) {
  return calcTypeLabel(type);
}


function isDraftEvent(event) {
  return canEditManagerEvent(event);
}

function eventDateForInput(value) {
  if (!value) return "";
  return String(value).slice(0, 10);
}

function getDraftEvent(event) {
  if (!event) return null;
  if (!state.managerDraftEventsById) state.managerDraftEventsById = {};
  const key = String(event.id);

  if (!state.managerDraftEventsById[key]) {
    state.managerDraftEventsById[key] = JSON.parse(JSON.stringify(event));
  } else {
    // Черновик хранит редактируемые поля карточки, но служебные поля соавторства
    // должны обновляться из свежего manager-dashboard после назначения/удаления соавтора.
    [
      "is_coauthored",
      "coauthor_name",
      "coauthor_user_id",
      "owner_manager_id",
      "owner_manager_name",
      "share_percent",
      "active_payment_requests_count",
      "payment_requests_count",
    ].forEach((field) => {
      if (Object.prototype.hasOwnProperty.call(event, field)) {
        state.managerDraftEventsById[key][field] = event[field];
      }
    });
  }

  return state.managerDraftEventsById[key];
}

function setDraftEventValue(eventId, field, value) {
  if (!state.managerDraftEventsById) state.managerDraftEventsById = {};
  const key = String(eventId);
  if (!state.managerDraftEventsById[key] && state.currentManagerEvent) {
    state.managerDraftEventsById[key] = JSON.parse(JSON.stringify(state.currentManagerEvent));
  }

  const event = state.managerDraftEventsById[key];
  if (!event) return;

  if (["agency_commission_amount", "simplified_bank_tax_percent"].includes(field)) {
    event[field] = normalizeNumberInput(value);
  } else {
    event[field] = value;
  }

  if (String(state.selectedManagerEventId) === key) {
    state.currentManagerEvent = { ...(state.currentManagerEvent || {}), ...event };
    updateCurrentManagerMiniCardLive();
  }
}

function getSelectedManagerEvent(data) {
  const events = data?.events || [];
  if (!events.length) return null;

  if (state.selectedManagerEventId) {
    const selected = events.find((event) => Number(event.id) === Number(state.selectedManagerEventId));
    if (selected) return selected;
  }

  return events[0];
}

function managerCardMetric(label, value) {
  const toneClass = ["Бюджет", "Доход"].includes(label) ? "mini-pill-green" : "";
  return `<span class="mini-pill ${toneClass}"><strong>${label}:</strong> ${value}</span>`;
}

function normalizeNumberInput(value) {
  const cleaned = String(value || "").replace(/\s/g, "").replace(",", ".");
  const number = Number(cleaned);
  return Number.isFinite(number) ? number : 0;
}


function setButtonLoading(button, isLoading, loadingText = "…") {
  if (!button) return;
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.disabled = true;
    button.textContent = loadingText;
    button.classList.add("is-loading");
    return;
  }

  button.disabled = false;
  button.textContent = button.dataset.originalText || button.textContent;
  button.classList.remove("is-loading");
  delete button.dataset.originalText;
}

function isButtonSoftLoadingAllowed(button) {
  if (!button || !(button instanceof HTMLElement)) return false;
  if (button.tagName !== "BUTTON") return false;
  if (button.disabled) return false;
  if (button.dataset.noSoftLoading === "true") return false;
  if (button.classList.contains("close-btn")) return false;
  return true;
}

function setSoftButtonLoading(button, isLoading) {
  if (!isButtonSoftLoadingAllowed(button)) return;

  if (isLoading) {
    button.classList.add("soft-loading");
    button.setAttribute("aria-busy", "true");
    return;
  }

  button.classList.remove("soft-loading");
  button.removeAttribute("aria-busy");
}

function installGlobalSoftButtonLoading() {
  if (window.__cfSoftButtonLoadingInstalled) return;
  window.__cfSoftButtonLoadingInstalled = true;

  const originalAddEventListener = EventTarget.prototype.addEventListener;

  EventTarget.prototype.addEventListener = function patchedAddEventListener(type, listener, options) {
    if (type !== "click" || typeof listener !== "function") {
      return originalAddEventListener.call(this, type, listener, options);
    }

    const wrappedListener = function wrappedSoftButtonClick(event) {
      const button = event?.target?.closest ? event.target.closest("button") : null;
      const shouldSoftLoad = isButtonSoftLoadingAllowed(button) && !button.classList.contains("is-loading");

      if (shouldSoftLoad) {
        setSoftButtonLoading(button, true);
      }

      let result;
      try {
        result = listener.call(this, event);
      } catch (error) {
        if (shouldSoftLoad) setSoftButtonLoading(button, false);
        throw error;
      }

      if (result && typeof result.finally === "function") {
        result.finally(() => {
          if (shouldSoftLoad) setSoftButtonLoading(button, false);
        });
      } else if (shouldSoftLoad) {
        window.setTimeout(() => setSoftButtonLoading(button, false), 450);
      }

      return result;
    };

    return originalAddEventListener.call(this, type, wrappedListener, options);
  };
}

installGlobalSoftButtonLoading();



async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;

  const response = await fetch(path, { ...options, headers });

  if (!response.ok) {
    let detail = `Ошибка ${response.status}`;
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch (_) {}
    throw new Error(detail);
  }

  return response.json();
}


let loadingCounter = 0;

function setLoading(isLoading, text = "Обновляем данные…") {
  const overlay = document.getElementById("loadingOverlay");
  if (!overlay) return;

  if (isLoading) {
    loadingCounter += 1;
    const span = overlay.querySelector("span");
    if (span) span.textContent = text;
    overlay.classList.remove("hidden");
    return;
  }

  loadingCounter = Math.max(0, loadingCounter - 1);
  if (loadingCounter === 0) overlay.classList.add("hidden");
}

async function withLoading(task, text = "Обновляем данные…") {
  setLoading(true, text);
  try {
    return await task();
  } finally {
    setLoading(false);
  }
}

function eventById(eventId) {
  const data = state.adminData;
  if (!data) return null;
  return (data.events || []).find((event) => Number(event.id) === Number(eventId)) || null;
}

function managerNameForRequest(request) {
  if (request.manager_name) return request.manager_name;

  const event = eventById(request.event_id);
  if (event?.manager_name) return event.manager_name;
  if (event?.manager_id) return managerNameById(event.manager_id);

  return "";
}

function clientNameForRequest(request) {
  if (request.client_name) return request.client_name;

  const event = eventById(request.event_id);
  if (event?.client_name) return event.client_name;

  return request.event_title || request.event_id || "";
}


function isInvoiceMethod(method) {
  const value = String(method || "").toLowerCase();
  return value === "invoice" || value === "по счету" || value === "по счёту";
}

function isSelfEmployedMethod(method) {
  const value = String(method || "").toLowerCase();
  return value === "self_employed" || value === "самозанятый";
}

function itemVatVisible(item) {
  return isInvoiceMethod(item.payment_method) ? item.vat_amount : 0;
}

function itemDeductionVisible(item) {
  if (isInvoiceMethod(item.payment_method)) {
    return item.deduction_amount || 0;
  }

  if (isSelfEmployedMethod(item.payment_method)) {
    const stored = asNumber(item.deduction_amount);
    if (stored > 0) return stored;

    const base = asNumber(item.amount_fact) > 0 ? asNumber(item.amount_fact) : asNumber(item.external_amount);
    return Math.round(base * 0.10 * 100) / 100;
  }

  return 0;
}


function calculationTypeValue(event, summary) {
  return String(
    event?.calculation_type ||
    event?.client_calculation_type ||
    summary?.calculation_type ||
    summary?.client_calculation_type ||
    ""
  ).toLowerCase();
}

function taxPercentLabelForEvent(event, summary) {
  if (summary?.tax_rate_percent !== undefined && summary?.tax_rate_percent !== null) {
    return `${Number(summary.tax_rate_percent).toFixed(Number(summary.tax_rate_percent) % 1 === 0 ? 0 : 2)}%`;
  }

  const type = calculationTypeValue(event, summary);
  const taxAmount = asNumber(summary?.internal_tax_amount) + asNumber(summary?.simplified_bank_tax_amount);

  if (type.includes("упрощ")) return "5%";
  if (type.includes("нал")) return "0%";
  if (type.includes("оур") || type.includes("contrast") || type.includes("ип")) return "12%";

  if (taxAmount <= 0) return "0%";
  return "12%";
}

function managerSalaryPaidValue(summary) {
  return (
    summary?.manager_salary_paid ||
    summary?.manager_paid_amount ||
    summary?.paid_manager_salary ||
    summary?.manager_payment_paid ||
    0
  );
}

function sortItemsCoordinatorFirst(items) {
  return [...(items || [])].sort((a, b) => {
    const aCoord = String(a.item_type || "").toLowerCase() === "coordinator" || String(a.external_name || "").toLowerCase().includes("координатор");
    const bCoord = String(b.item_type || "").toLowerCase() === "coordinator" || String(b.external_name || "").toLowerCase().includes("координатор");

    if (aCoord && !bCoord) return -1;
    if (!aCoord && bCoord) return 1;

    return Number(a.sort_order || a.id || 0) - Number(b.sort_order || b.id || 0);
  });
}

function modalFilteredRequests(requests, status) {
  if (!status || status === "all") return requests || [];
  if (status === "active") {
    return (requests || []).filter((request) => !["rejected", "cash_received"].includes(request.status));
  }
  if (status === "archive") {
    return (requests || []).filter((request) => ["rejected", "cash_received"].includes(request.status));
  }
  return (requests || []).filter((request) => request.status === status);
}

function renderEventPaymentRequestsTable(requests, selectedStatus = "all") {
  const filtered = modalFilteredRequests(requests || [], selectedStatus);

  return `
    <div class="block-title">
      <h3>Заявки мероприятия</h3>
      <span class="muted">${filtered.length} из ${(requests || []).length} шт.</span>
    </div>

    <div class="filters-row">
      <label class="compact-label">Статус оплаты
        <select id="eventModalRequestStatusFilter">
          <option value="all" ${selectedStatus === "all" ? "selected" : ""}>Все</option>
          <option value="active" ${selectedStatus === "active" ? "selected" : ""}>Активные</option>
          <option value="new" ${selectedStatus === "new" ? "selected" : ""}>Новая</option>
          <option value="paid" ${selectedStatus === "paid" ? "selected" : ""}>Оплачено</option>
          <option value="cash_received" ${selectedStatus === "cash_received" ? "selected" : ""}>Деньги в кассе</option>
          <option value="rejected" ${selectedStatus === "rejected" ? "selected" : ""}>Отменено</option>
        </select>
      </label>
    </div>

    ${filtered.length ? `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Менеджер</th>
              <th>Позиция</th>
              <th>Сумма заявки</th>
              <th>Способ</th>
              <th>Налоговый статус</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map((request) => `
              <tr>
                <td>${managerNameForRequest(request)}</td>
                <td>${request.position || request.item_name_snapshot || ""}</td>
                <td><div class="request-main-amount">${formatMoney(request.amount_requested)}</div></td>
                <td>${paymentMethodLabel(request.payment_method)}</td>
                <td>${request.tax_status || request.tax_status_label || ""}</td>
                <td><span class="status ${request.status}">${statusLabel(request.status)}</span></td>
                <td>
                  <div class="inline-actions">
                    ${adminRequestActions(request)}
                    ${canManagerCancelRequest(request) ? `<button class="small danger" data-cancel-request="${request.id}">Отменить</button>` : ""}
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    ` : `<div class="empty-state">По выбранному статусу заявок нет.</div>`}
  `;
}

function attachEventModalRequestFilter(requests) {
  const select = document.getElementById("eventModalRequestStatusFilter");
  if (!select) return;

  select.addEventListener("change", () => {
    const holder = document.getElementById("eventModalRequestsSection");
    if (!holder) return;

    holder.innerHTML = renderEventPaymentRequestsTable(requests, select.value);
    attachPaymentRequestActions();
    attachEventModalRequestFilter(requests);
  });
}


function attachManagerSalaryRequestButton() {
  document.querySelectorAll("[data-manager-salary-request]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const [eventId, amount] = button.getAttribute("data-manager-salary-request").split(":");
      await createManagerSalaryRequest(eventId, amount);
    });
  });
}

function activePaymentRequests(requests) {
  return (requests || []).filter((request) => !["rejected", "cash_received"].includes(request.status));
}

function archivedPaymentRequests(requests) {
  return (requests || []).filter((request) => ["rejected", "cash_received"].includes(request.status));
}



function resetLoginButton() {
  const button = $("loginBtn");
  if (!button) return;
  button.disabled = false;
  button.textContent = "Войти";
  button.classList.remove("is-loading");
  delete button.dataset.originalText;
}

function setAuthMode(mode) {
  state.authMode = mode || "manager";

  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.classList.toggle("active", button.getAttribute("data-auth-mode") === state.authMode);
  });

  const nameLabel = $("loginNameLabel");
  const nameInput = $("loginName");
  const pinInput = $("loginPin");

  if (nameLabel) {
    nameLabel.style.display = state.authMode === "admin" ? "none" : "block";
    nameLabel.childNodes[0].nodeValue = state.authMode === "department_head" ? "Имя руководителя" : "Имя менеджера";
  }

  if (nameInput) {
    nameInput.placeholder = state.authMode === "department_head" ? "Санжар или Рауфаль" : "Имя";
    if (state.authMode === "admin") nameInput.value = "";
  }

  if (pinInput) {
    pinInput.placeholder = "••••";
    if (state.authMode === "admin") pinInput.focus();
  }

  const error = $("loginError");
  if (error) {
    error.textContent = "";
    error.classList.add("hidden");
  }

  resetLoginButton();
}

function getLoginAttempts() {
  const pin = $("loginPin").value;
  const name = ($("loginName")?.value || "").trim();

  return [{
    name: state.authMode === "admin" ? null : (name || null),
    phone: null,
    pin,
    auth_mode: state.authMode || "manager",
  }];
}

function attachAuthTabs() {
  document.querySelectorAll("[data-auth-mode]").forEach((button) => {
    button.onclick = () => setAuthMode(button.getAttribute("data-auth-mode"));
  });
}


function managerEditableDepartments() {
  const departments = managerEditableDepartments();
  const filtered = departments.filter((department) => {
    const name = String(department.name || "").toLowerCase();
    return name.includes("санжар") || name.includes("рауф");
  });
  return filtered.length ? filtered : departments.filter((department) => department.is_active !== false);
}

function formatPhoneDisplay(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";

  if (raw.startsWith("+")) return raw;

  const digits = raw.replace(/\D/g, "");
  if (!digits) return raw;

  if (digits.length === 11 && digits.startsWith("8")) {
    return `+7${digits.slice(1)}`;
  }

  if (digits.startsWith("7")) {
    return `+${digits}`;
  }

  return `+${digits}`;
}

function phoneDigitsForKz(value) {
  let digits = String(value || "").replace(/\D/g, "");

  if (digits.startsWith("8")) {
    digits = `7${digits.slice(1)}`;
  }

  if (!digits.startsWith("7")) {
    digits = `7${digits}`;
  }

  return digits.slice(0, 11);
}

function formatPhoneKzPretty(value) {
  const digits = phoneDigitsForKz(value);
  const rest = digits.startsWith("7") ? digits.slice(1) : digits;

  if (!rest) return "+7";

  const p1 = rest.slice(0, 3);
  const p2 = rest.slice(3, 6);
  const p3 = rest.slice(6, 8);
  const p4 = rest.slice(8, 10);

  let result = "+7";
  if (p1) result += ` (${p1}`;
  if (p1.length === 3) result += ")";
  if (p2) result += ` ${p2}`;
  if (p3) result += ` ${p3}`;
  if (p4) result += ` ${p4}`;

  return result;
}

function formatPhoneInputLive(input) {
  if (!input) return;
  input.value = formatPhoneKzPretty(input.value);
}

function renderUserBadgeContent(user) {
  const name = user?.name || "";

  return `
    <span class="user-badge-main">
      <span class="user-badge-line">${name}</span>
      <span class="user-badge-role">${roleLabel(user?.role)}</span>
    </span>
    ${user?.role === "manager" ? `<button class="user-badge-edit" id="headerProfileEditBtn" type="button" title="Редактировать данные">✎</button>` : ""}
  `;
}

function updateHeaderUserInfo(user) {
  if (!user) return;
  document.body.classList.toggle("admin-mode", user.role === "admin");
  $("pageTitle").textContent = roleLabel(user.role);
  $("pageSubtitle").textContent = user.role === "admin"
    ? "Проверка мероприятий, заявки, планы и закрытие месяца"
    : "";

  const userBadge = $("userBadge");
  if (userBadge) {
    if (user.role === "admin") {
      userBadge.innerHTML = "";
      userBadge.classList.add("hidden");
      userBadge.classList.add("admin-hidden");
    } else {
      userBadge.innerHTML = renderUserBadgeContent(user);
      userBadge.classList.remove("hidden");
      userBadge.classList.remove("admin-hidden");
    }
  }

  const editBtn = document.getElementById("headerProfileEditBtn");
  if (editBtn) editBtn.addEventListener("click", openManagerProfileModal);
}


function showLogin() {
  $("loginScreen").classList.remove("hidden");
  $("dashboardScreen").classList.add("hidden");
  $("logoutBtn").classList.add("hidden");
  $("userBadge").classList.add("hidden");
  $("adminTabs").classList.add("hidden");
  $("pageTitle").textContent = "Вход";
  $("pageSubtitle").textContent = "Финансовая панель мероприятий";
  attachLoginHandlers();
  setAuthMode(state.authMode || "manager");
  resetLoginButton();
}

function showDashboardShell() {
  $("loginScreen").classList.add("hidden");
  $("dashboardScreen").classList.remove("hidden");
  $("logoutBtn").classList.remove("hidden");

  const user = state.bootstrap?.user;
  const userBadge = $("userBadge");
  if (userBadge) {
    if (user?.role === "admin") userBadge.classList.add("hidden");
    else userBadge.classList.remove("hidden");
  }
}

function metric(label, value) {
  return `<div class="card metric"><div class="label">${label}</div><div class="value">${value}</div></div>`;
}

function renderSummary(cards) {
  $("summaryCards").innerHTML = cards.map(([label, value]) => metric(label, value)).join("");
}

function progressLine(percent) {
  const p = Math.max(0, Math.min(100, Number(percent || 0)));
  return `<div class="progress-line" style="--progress:${p}%"><span></span></div>`;
}

function getDepartmentsMap() {
  const map = new Map();
  (state.bootstrap?.departments || []).forEach((department) => map.set(Number(department.id), department.name));
  return map;
}

function getManagers() {
  return (state.users || []).filter((user) => user.role === "manager" && user.is_active);
}

function managerNameById(id) {
  const user = (state.users || []).find((item) => Number(item.id) === Number(id));
  return user?.name || "";
}

function departmentNameById(id) {
  return getDepartmentsMap().get(Number(id)) || "";
}

function departmentClassByName(name) {
  const value = String(name || "").toLowerCase();
  if (value.includes("санжар")) return "department-sanzhar";
  if (value.includes("рауф")) return "department-raufal";
  return "";
}

function departmentClassById(id) {
  return departmentClassByName(departmentNameById(id));
}

function filteredEvents(events) {
  let list = [...(events || [])];

  if (state.eventDepartmentFilter !== "all") {
    list = list.filter((event) => Number(event.department_id) === Number(state.eventDepartmentFilter));
  }

  if (state.eventManagerFilter !== "all") {
    list = list.filter((event) => Number(event.manager_id) === Number(state.eventManagerFilter));
  }

  if (state.eventStatusFilter !== "all") {
    list = list.filter((event) => event.status === state.eventStatusFilter);
  }

  const search = String(state.eventSearch || "").trim().toLowerCase();
  if (search) {
    list = list.filter((event) => String(event.client_name || "").toLowerCase().includes(search));
  }

  return list;
}

function filteredPaymentRequests(requests, mode = "regular") {
  let list = [...(requests || [])];

  if (mode === "archive") {
    if (state.paymentStatusFilter === "all" || state.paymentStatusFilter === "active") {
      list = list.filter((request) => ["rejected", "cash_received"].includes(request.status));
    } else {
      list = list.filter((request) => request.status === state.paymentStatusFilter);
    }
  } else {
    if (state.paymentStatusFilter === "active" || state.paymentStatusFilter === "all") {
      list = list.filter((request) => !["rejected", "cash_received"].includes(request.status));
    } else {
      list = list.filter((request) => request.status === state.paymentStatusFilter);
    }
  }

  if (state.paymentCustomerFilter && state.paymentCustomerFilter !== "all") {
    list = list.filter((request) => String(clientNameForRequest(request) || "") === String(state.paymentCustomerFilter));
  }

  if (state.paymentManagerFilter && state.paymentManagerFilter !== "all") {
    list = list.filter((request) => String(managerNameForRequest(request) || "") === String(state.paymentManagerFilter));
  }

  return list;
}

function renderAdminTabs() {
  const tabs = [
    ["overview", "Обзор"],
    ["events", "Мероприятия"],
    ["requests", "Заявки"],
    ["requests_archive", "Архив заявок"],
    ["plans", "Задать планы"],
    ["closing", "Закрыть месяц"],
  ];

  $("adminTabs").classList.remove("hidden");
  $("adminTabs").innerHTML = tabs.map(([key, label]) => `
    <button class="tab-btn ${state.activeAdminTab === key ? "active" : ""}" data-admin-tab="${key}">
      ${label}
    </button>
  `).join("");

  document.querySelectorAll("[data-admin-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeAdminTab = button.getAttribute("data-admin-tab");
      state.paymentStatusFilter = state.activeAdminTab === "requests_archive" ? "all" : "active";
      state.paymentCustomerFilter = "all";
      state.paymentManagerFilter = "all";
      setLoading(true, "Переключаем вкладку…");
      setTimeout(() => {
        try {
          renderAdminDashboard(state.adminData);
        } finally {
          setLoading(false);
        }
      }, 80);
    });
  });
}

function renderEventsTable(events, allowClick = false) {
  if (!events || !events.length) return `<div class="empty-state">Нет мероприятий за выбранный месяц.</div>`;

  return `
    <div class="table-wrap admin-events-table-wrap">
      <table class="admin-events-table">
        <thead>
          <tr>
            <th>Дата</th><th>Заказчик</th><th>Мероприятие</th><th>Менеджер</th><th>Статус</th>
            <th>Оборот</th><th>Доход</th><th>ЗП менеджера</th><th>Заявки</th>
          </tr>
        </thead>
        <tbody>
          ${events.map((event) => `
            <tr class="${allowClick ? "clickable-row" : ""} admin-event-row ${eventStatusToneClass(event.status)} ${departmentClassById(event.department_id)}" ${allowClick ? `data-event-id="${event.id}"` : ""}>
              <td class="nowrap">${formatDateRu(event.event_date) || event.event_date || ""}</td>
              <td><strong>${event.client_name || ""}</strong></td>
              <td>${event.title || ""}</td>
              <td>${event.manager_name || managerNameById(event.manager_id) || ""}</td>
              <td><span class="status ${event.status} admin-event-status-badge">${statusLabel(event.status)}</span></td>
              <td>${formatMoney(event.external_total)}</td>
              <td>${formatMoney(event.final_company_income)}</td>
              <td>${formatMoney(event.manager_salary || 0)}</td>
              <td>${event.active_payment_requests_count ?? event.payment_requests_count ?? 0}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderEventFilters(events) {
  const managers = getManagers();
  const statuses = [...new Set((events || []).map((event) => event.status).filter(Boolean))];

  return `
    <div class="filters-row">
      <label class="compact-label">Отдел
        <select id="eventDepartmentFilter">
          <option value="all">Все отделы</option>
          ${(state.bootstrap?.departments || []).map((department) => `
            <option value="${department.id}" ${String(state.eventDepartmentFilter) === String(department.id) ? "selected" : ""}>${department.name}</option>
          `).join("")}
        </select>
      </label>

      <label class="compact-label">Менеджер
        <select id="eventManagerFilter">
          <option value="all">Все менеджеры</option>
          ${managers.map((manager) => `
            <option value="${manager.id}" ${String(state.eventManagerFilter) === String(manager.id) ? "selected" : ""}>${manager.name}</option>
          `).join("")}
        </select>
      </label>

      <label class="compact-label">Статус
        <select id="eventStatusFilter">
          <option value="all">Все статусы</option>
          ${statuses.map((status) => `
            <option value="${status}" ${state.eventStatusFilter === status ? "selected" : ""}>${statusLabel(status)}</option>
          `).join("")}
        </select>
      </label>

      <label class="compact-label search-label">Поиск по заказчику
        <input id="eventSearch" value="${state.eventSearch || ""}" placeholder="Название заказчика" />
      </label>
    </div>
  `;
}



function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function uniqueSortedValues(values) {
  return [...new Set((values || []).map((value) => String(value || "").trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, "ru"));
}

function paymentCustomerFilterOptions(requests, mode = "regular") {
  const base = mode === "archive" ? archivedPaymentRequests(requests) : activePaymentRequests(requests);
  return uniqueSortedValues(base.map((request) => clientNameForRequest(request)));
}

function paymentManagerFilterOptions(requests, mode = "regular") {
  const base = mode === "archive" ? archivedPaymentRequests(requests) : activePaymentRequests(requests);
  return uniqueSortedValues(base.map((request) => managerNameForRequest(request)));
}

function selectOptions(values, selectedValue, allLabel) {
  return `
    <option value="all" ${selectedValue === "all" || !selectedValue ? "selected" : ""}>${allLabel}</option>
    ${values.map((value) => `
      <option value="${escapeHtml(value)}" ${String(selectedValue) === String(value) ? "selected" : ""}>${escapeHtml(value)}</option>
    `).join("")}
  `;
}


function renderPaymentFilters(requests = [], mode = "regular") {
  const customerOptions = paymentCustomerFilterOptions(requests, mode);
  const managerOptions = paymentManagerFilterOptions(requests, mode);

  const regularOptions = `
    <option value="active" ${state.paymentStatusFilter === "active" ? "selected" : ""}>Активные</option>
    <option value="new" ${state.paymentStatusFilter === "new" ? "selected" : ""}>Новая</option>
    <option value="paid" ${state.paymentStatusFilter === "paid" ? "selected" : ""}>Оплачено</option>
  `;

  const archiveOptions = `
    <option value="all" ${state.paymentStatusFilter === "all" || state.paymentStatusFilter === "active" ? "selected" : ""}>Весь архив</option>
    <option value="cash_received" ${state.paymentStatusFilter === "cash_received" ? "selected" : ""}>Деньги в кассе</option>
    <option value="rejected" ${state.paymentStatusFilter === "rejected" ? "selected" : ""}>Отменено</option>
  `;

  return `
    <div class="filters-row">
      <label class="compact-label">Статус оплаты
        <select id="paymentStatusFilter">
          ${mode === "archive" ? archiveOptions : regularOptions}
        </select>
      </label>

      <label class="compact-label">Заказчик
        <select id="paymentCustomerFilter">
          ${selectOptions(customerOptions, state.paymentCustomerFilter, "Все заказчики")}
        </select>
      </label>

      <label class="compact-label">Менеджер
        <select id="paymentManagerFilter">
          ${selectOptions(managerOptions, state.paymentManagerFilter, "Все менеджеры")}
        </select>
      </label>
    </div>
  `;
}

function canManagerCancelRequest(request) {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "manager") return false;
  return !["paid", "cash_received", "rejected"].includes(request.status);
}

function adminRequestActions(request) {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return "";

  const status = request.status;
  const buttons = [];

  if (status === "new" || status === "tax_check_needed" || status === "to_pay") {
    buttons.push(`<button class="small" data-set-request-status="${request.id}:paid">Оплачено</button>`);
    buttons.push(`<button class="small danger" data-set-request-status="${request.id}:rejected">Отменить</button>`);
  } else if (status === "paid") {
    buttons.push(`<button class="small secondary" data-set-request-status="${request.id}:cash_received">Деньги в кассе</button>`);
    buttons.push(`<button class="small danger" data-set-request-status="${request.id}:rejected">Возврат</button>`);
  } else if (status === "cash_received") {
    buttons.push(`<button class="small danger" data-set-request-status="${request.id}:rejected">Возврат</button>`);
  }

  return buttons.join("");
}


function requestsForCurrentUser(requests) {
  return requests || [];
}


function paymentRequestPositionKey(request) {
  return String(request.event_item_id || request.item_id || request.position || request.item_name_snapshot || "manager_salary");
}

function paymentRequestPositionName(request) {
  return request.position || request.item_name_snapshot || "Позиция";
}

function groupedPaymentRequestsByPosition(requests) {
  const groups = [];
  const index = new Map();

  (requests || []).forEach((request) => {
    const key = paymentRequestPositionKey(request);
    if (!index.has(key)) {
      const group = {
        key,
        title: paymentRequestPositionName(request),
        requests: [],
      };
      groups.push(group);
      index.set(key, group);
    }
    index.get(key).requests.push(request);
  });

  groups.forEach((group) => {
    group.requests.sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
  });

  return groups;
}


function eventPaymentRequestsForManager(eventId) {
  return requestsForCurrentUser(state.managerPaymentRequests || [])
    .filter((request) => Number(request.event_id) === Number(eventId))
    .sort((a, b) => {
      const posA = paymentRequestPositionName(a).localeCompare(paymentRequestPositionName(b), "ru");
      if (posA !== 0) return posA;
      return Number(b.id || 0) - Number(a.id || 0);
    });
}


function managerRequestCancelButtonHtml(request) {
  const canCancel = canManagerCancelEventRequest(request);
  return `<button class="small danger manager-request-cancel-btn" data-manager-event-request-cancel="${request.id}" ${canCancel ? "" : "disabled"}>Отменить</button>`;
}


function canManagerCancelEventRequest(request) {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "manager") return false;
  return !["paid", "cash_received", "rejected"].includes(request.status);
}

function renderManagerPaymentRequestsModal(eventId) {
  const requests = eventPaymentRequestsForManager(eventId);
  const groups = groupedPaymentRequestsByPosition(requests);

  if (!requests.length) {
    return `
      <div class="manager-event-requests-modal">
        <div class="empty-state">По этому мероприятию заявок пока нет.</div>
      </div>
    `;
  }

  return `
    <div class="manager-event-requests-modal compact-payments-modal grouped-payments-modal compact-grouped-payments">
      ${groups.map((group) => `
        <div class="manager-payment-position-group compact">
          <div class="manager-payment-position-title compact">
            <span>${group.title}</span>
            <em>${group.requests.length} заявк${group.requests.length === 1 ? "а" : "и"}</em>
          </div>

          <div class="manager-event-requests-list compact">
            ${group.requests.map((request) => `
              <div class="manager-payment-request-row compact">
                <div class="manager-payment-request-amount">
                  ${formatMoney(request.amount_requested)}
                </div>
                <div class="manager-payment-request-method">
                  ${paymentMethodLabel(request.payment_method)}
                </div>
                <div class="manager-payment-request-status">
                  <span class="status ${request.status}">${statusLabel(request.status)}</span>
                </div>
                <div class="manager-payment-request-action">
                  ${managerRequestCancelButtonHtml(request)}
                </div>
              </div>
            `).join("")}
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

async function openManagerPaymentRequestsModal(eventId) {
  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

  await refreshManagerPaymentRequestsForEvent(eventId);

  backdrop.classList.remove("pin-modal-mode");
  backdrop.classList.remove("profile-modal-mode");
  backdrop.classList.remove("payment-modal-mode");
  backdrop.classList.add("manager-requests-modal-mode");
  backdrop.classList.remove("hidden");

  title.textContent = "Мои оплаты";
  content.innerHTML = renderManagerPaymentRequestsModal(eventId);

  content.querySelectorAll("[data-manager-event-request-cancel]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.disabled) return;

      const requestId = button.getAttribute("data-manager-event-request-cancel");
      if (!confirm(`Отменить заявку #${requestId}?`)) return;

      try {
        setButtonLoading(button, true, "Отменяем…");
        await api(`/payment-requests/${requestId}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: "rejected" }),
        });
        showToast("Заявка отменена");
        await refreshManagerPaymentRequestsForEvent(eventId);
        content.innerHTML = renderManagerPaymentRequestsModal(eventId);
        await renderManagerEventDetail(eventId, { noLoading: true });
      } catch (error) {
        alert(error.message || "Не удалось отменить заявку");
      } finally {
        if (button.isConnected) setButtonLoading(button, false);
      }
    });
  });
}


function renderPaymentRequestsTable(requests, title = "Заявки на оплату", mode = "regular") {
  const baseRequests = mode === "archive" ? archivedPaymentRequests(requests) : activePaymentRequests(requests);
  const filteredRequests = filteredPaymentRequests(requests, mode);

  if (!baseRequests.length) {
    return `
      <div class="block-title"><h3>${title}</h3></div>
      ${renderPaymentFilters(requests, mode)}
      <div class="empty-state">Заявок пока нет.</div>
    `;
  }

  if (!filteredRequests.length) {
    return `
      <div class="block-title">
        <h3>${title}</h3>
        <span class="muted">0 из ${baseRequests.length} шт.</span>
      </div>
      ${renderPaymentFilters(requests, mode)}
      <div class="empty-state">По выбранным фильтрам заявок нет.</div>
    `;
  }

  return `
    <div class="block-title">
      <h3>${title}</h3>
      <span class="muted">${filteredRequests.length} из ${baseRequests.length} шт.</span>
    </div>
    ${renderPaymentFilters(requests, mode)}
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Менеджер</th>
            <th>Заказчик</th>
            <th>Позиция</th>
            <th>Сумма заявки</th>
            <th>Способ</th>
            <th>Налоговый статус</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          ${filteredRequests.map((request) => `
            <tr>
              <td>${managerNameForRequest(request)}</td>
              <td><strong>${clientNameForRequest(request)}</strong></td>
              <td>${request.position || request.item_name_snapshot || ""}</td>
              <td><div class="request-main-amount">${formatMoney(request.amount_requested)}</div></td>
              <td>${paymentMethodLabel(request.payment_method)}</td>
              <td>${request.tax_status || request.tax_status_label || ""}</td>
              <td><span class="status ${request.status}">${statusLabel(request.status)}</span></td>
              <td>
                <div class="inline-actions">
                  ${adminRequestActions(request)}
                  ${canManagerCancelRequest(request) ? `<button class="small danger" data-cancel-request="${request.id}">Отменить</button>` : ""}
                </div>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function attachFilters() {
  const paymentStatus = document.getElementById("paymentStatusFilter");
  if (paymentStatus) {
    paymentStatus.addEventListener("change", (event) => {
      state.paymentStatusFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const paymentCustomer = document.getElementById("paymentCustomerFilter");
  if (paymentCustomer) {
    paymentCustomer.addEventListener("change", (event) => {
      state.paymentCustomerFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const paymentManager = document.getElementById("paymentManagerFilter");
  if (paymentManager) {
    paymentManager.addEventListener("change", (event) => {
      state.paymentManagerFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const eventDepartment = document.getElementById("eventDepartmentFilter");
  if (eventDepartment) {
    eventDepartment.addEventListener("change", async (event) => {
      state.eventDepartmentFilter = event.target.value;
      await withLoading(loadDashboard, "Фильтруем мероприятия…");
    });
  }

  const eventManager = document.getElementById("eventManagerFilter");
  if (eventManager) {
    eventManager.addEventListener("change", async (event) => {
      state.eventManagerFilter = event.target.value;
      await withLoading(loadDashboard, "Фильтруем мероприятия…");
    });
  }

  const eventStatus = document.getElementById("eventStatusFilter");
  if (eventStatus) {
    eventStatus.addEventListener("change", async (event) => {
      state.eventStatusFilter = event.target.value;
      await withLoading(loadDashboard, "Фильтруем мероприятия…");
    });
  }

  const eventSearch = document.getElementById("eventSearch");
  if (eventSearch) {
    eventSearch.addEventListener("input", (event) => {
      state.eventSearch = event.target.value;
      clearTimeout(window.__cfEventSearchTimer);
      window.__cfEventSearchTimer = setTimeout(() => {
        withLoading(loadDashboard, "Ищем…").catch((error) => alert(error.message));
      }, 350);
    });
  }
}

function attachPaymentRequestActions() {
  document.querySelectorAll("[data-cancel-request]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.getAttribute("data-cancel-request");
      if (!confirm(`Отменить заявку #${id}?`)) return;

      try {
        await api(`/payment-requests/${id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: "rejected" }),
        });
        await withLoading(loadDashboard, "Обновляем данные…");
      } catch (error) {
        alert(error.message);
      }
    });
  });

  document.querySelectorAll("[data-set-request-status]").forEach((button) => {
    button.addEventListener("click", async () => {
      const raw = button.getAttribute("data-set-request-status");
      const [id, status] = raw.split(":");

      const labels = {
        paid: "отметить оплаченной",
        cash_received: "отметить деньги в кассе",
        rejected: "отменить / оформить возврат",
      };

      if (!confirm(`Заявку #${id} ${labels[status] || "изменить"}?`)) return;

      try {
        await api(`/payment-requests/${id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status }),
        });
        await withLoading(loadDashboard, "Обновляем данные…");
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

function attachEventRows() {
  document.querySelectorAll("[data-event-id]").forEach((row) => {
    row.addEventListener("click", async () => {
      await openEventModal(row.getAttribute("data-event-id"));
    });
  });
}


function canRequestManagerSalaryForEvent(event) {
  const user = state.bootstrap?.user;
  if (!user || !event) return false;

  if (user.role === "admin") return true;
  if (user.role === "manager" && Number(event.manager_id) === Number(user.id)) return true;

  return false;
}

async function createManagerSalaryRequest(eventId, defaultAmount) {
  const rawAmount = prompt("Сумма заявки на ЗП менеджера", String(Math.max(0, Math.round(asNumber(defaultAmount)))));
  if (rawAmount === null) return;

  const amount = Number(String(rawAmount).replace(/\s/g, "").replace(",", "."));
  if (!amount || amount <= 0) {
    alert("Сумма должна быть больше 0");
    return;
  }

  const comment = prompt("Комментарий к заявке", "ЗП менеджера") || "ЗП менеджера";

  await withLoading(async () => {
    await api(`/events/${eventId}/manager-salary/payment-requests`, {
      method: "POST",
      body: JSON.stringify({
        amount_requested: amount,
        payment_method: "cash",
        card_number: null,
        comment,
      }),
    });
    await openEventModal(eventId);
    await loadDashboard();
  }, "Создаём заявку на ЗП менеджера…");
}

async function openEventModal(eventId) {
  $("eventModalBackdrop").classList.remove("pin-modal-mode");
  $("eventModalBackdrop").classList.remove("profile-modal-mode");
  $("eventModalBackdrop").classList.remove("payment-modal-mode");
  $("eventModalBackdrop").classList.remove("hidden");
  $("eventModalTitle").textContent = `Мероприятие #${eventId}`;
  $("eventModalContent").innerHTML = `<div class="empty-state">Загрузка...</div>`;

  try {
    const [event, summary, items, requests] = await Promise.all([
      api(`/events/${eventId}`),
      api(`/events/${eventId}/summary`),
      api(`/events/${eventId}/items`),
      api(`/events/${eventId}/payment-requests`),
    ]);

    $("eventModalTitle").textContent = `${event.client_name} · ${event.title}`;

    const sortedItems = sortItemsCoordinatorFirst((items || []).filter((item) => item.item_type !== "manager_salary"));
    const taxesAmount = asNumber(summary.taxes_total ?? (asNumber(summary.internal_tax_amount) + asNumber(summary.simplified_bank_tax_amount)));
    const managerSalary = asNumber(summary.manager_salary);
    const managerSalaryPaid = asNumber(managerSalaryPaidValue(summary));
    const managerSalaryRemaining = Math.max(0, managerSalary - managerSalaryPaid);

    $("eventModalContent").innerHTML = `
      <div class="grid cards modal-metric-cards">
        ${metric("Оборот", formatMoney(summary.turnover_with_vat ?? summary.external_total))}
        ${metric(`Налоги ${taxPercentLabelForEvent(event, summary)}`, formatMoney(taxesAmount))}
        ${metric("НДС", formatMoney(summary.vat_to_pay ?? summary.vat_total))}
        ${metric("Оплачено", formatMoney(summary.paid_total))}
        <div class="card metric income-metric">
          <div class="label">Доход компании</div>
          <div class="value">${formatMoney(summary.final_company_income)}</div>
        </div>
      </div>

      <div class="divider"></div>

      <h3>Смета</h3>
      <div class="table-wrap estimate-table-wrap">
        <table class="estimate-table">
          <thead>
            <tr>
              <th>Позиция</th><th>Смета</th><th>Факт</th><th>Оплата</th><th>Способ</th><th>НДС</th><th>Вычеты</th>
            </tr>
          </thead>
          <tbody>
            ${sortedItems.map((item) => `
              <tr>
                <td><strong>${item.external_name}</strong></td>
                <td>${formatMoney(item.external_amount)}</td>
                <td>${formatMoney(item.amount_fact)}</td>
                <td>${formatMoney(item.paid_amount)}</td>
                <td>${paymentMethodLabel(item.payment_method)}</td>
                <td>${formatMoney(itemVatVisible(item))}</td>
                <td>${formatMoney(itemDeductionVisible(item))}</td>
              </tr>
            `).join("")}
            <tr class="manager-salary-row">
              <td>
                <strong>Менеджер 21%</strong>
                ${canRequestManagerSalaryForEvent(event) && managerSalaryRemaining > 0 ? `<button class="small secondary salary-request-btn" data-manager-salary-request="${event.id}:${managerSalaryRemaining}">Подать заявку</button>` : ""}
              </td>
              <td>0</td>
              <td>${formatMoney(managerSalary)}</td>
              <td>${formatMoney(managerSalaryPaid)}</td>
              <td>ЗП менеджера</td>
              <td>0</td>
              <td>0</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div id="eventModalRequestsSection">
        ${renderEventPaymentRequestsTable(requests || [], "all")}
      </div>
    `;

    attachPaymentRequestActions();
    attachEventModalRequestFilter(requests || []);
    attachManagerSalaryRequestButton();
  } catch (error) {
    $("eventModalContent").innerHTML = `<div class="error">${error.message}</div>`;
  }
}

function renderAdminOverview(data) {
  const managers = getManagers();

  const managerStats = managers.map((manager) => {
    const events = (data.events || []).filter((event) => Number(event.manager_id) === Number(manager.id));
    const income = events.reduce((sum, event) => sum + asNumber(event.final_company_income), 0);
    const plan = asNumber(data.manager_personal_plan_amount);
    const percent = plan > 0 ? Math.round((income / plan) * 10000) / 100 : 0;

    return {
      manager,
      income,
      plan,
      percent,
      departmentId: manager.department_id,
      departmentName: departmentNameById(manager.department_id),
    };
  });

  const departments = data.departments || [];
  const companyPlan = asNumber(data.company_plan_amount);
  const companyFact = asNumber(data.company_fact_income_amount);
  const companyPercent = companyPlan > 0 ? Math.round((companyFact / companyPlan) * 10000) / 100 : 0;

  return `
    <section class="overview-company-card">
      <div class="overview-card-top">
        <div>
          <div class="overview-label">Общий план</div>
          <div class="overview-big-number">${formatMoney(companyFact)} ₸</div>
          <div class="overview-subline">Цель: ${formatMoney(companyPlan)} ₸ · ${companyPercent}%</div>
        </div>
        <div class="overview-company-title">Компания</div>
      </div>
      ${progressLine(companyPercent)}
    </section>

    <section class="overview-departments-grid">
      ${departments.map((dep) => {
        const depClass = departmentClassByName(dep.department_name);
        const depManagers = managerStats.filter((row) => Number(row.departmentId) === Number(dep.department_id));

        return `
          <article class="department-overview-card ${depClass}">
            <div class="department-card-head">
              <div>
                <div class="overview-label">Отдел</div>
                <h3>${dep.department_name}</h3>
              </div>
              <div class="department-total">
                <div>${formatMoney(dep.fact_income_amount)} ₸</div>
                <span>${dep.completion_percent}% · цель ${formatMoney(dep.plan_amount)} ₸</span>
              </div>
            </div>

            ${progressLine(dep.completion_percent)}

            <div class="manager-progress-list">
              ${depManagers.length ? depManagers.map((row) => `
                <div class="manager-progress-row">
                  <div class="manager-progress-main">
                    <strong>${row.manager.name}</strong>
                    <span>${formatMoney(row.income)} ₸ · ${row.percent}%</span>
                  </div>
                  <div class="manager-progress-bar">
                    ${progressLine(row.percent)}
                  </div>
                </div>
              `).join("") : `<div class="empty-state">Менеджеров в отделе пока нет.</div>`}
            </div>
          </article>
        `;
      }).join("")}
    </section>
  `;
}

function renderAdminEvents(data) {
  const events = filteredEvents(data.events || []);
  return `
    ${renderEventFilters(data.events || [])}
    ${renderEventsTable(events, true)}
  `;
}

function renderPlansSkeleton(data) {
  return `
    <div class="block-title">
      <h3>Планы</h3>
      <button id="openPlansModalBtn" class="secondary">Задать планы</button>
    </div>
    <div class="empty-state">
      Скелет готов: здесь будет редактирование общего плана, долей отделов и индивидуальных планов менеджеров.
      Сохранение подключим следующим шагом к backend-ручкам планов.
    </div>
    <div class="overview-section">
      <h3>Текущие значения</h3>
      <div class="grid cards">
        ${metric("План компании", formatMoney(data.company_plan_amount))}
        ${metric("Личный план менеджера", formatMoney(data.manager_personal_plan_amount))}
        ${metric("Санжар", "2/3")}
        ${metric("Рауфаль", "1/3")}
      </div>
    </div>
  `;
}

function renderClosingSkeleton(data) {
  return `
    <div class="block-title">
      <h3>Закрыть месяц</h3>
    </div>
    <div class="empty-state">
      Здесь будет ввод расходов и закрытие месяца. По умолчанию расход делится: Санжар 2/3, Рауфаль 1/3.
      Для каждой позиции будет выбор: по умолчанию / 100% Санжар / 100% Рауфаль / вручную.
    </div>

    <div class="overview-section">
      <h3>Текущее закрытие</h3>
      <div class="grid cards">
        ${metric("Расходы компании", formatMoney(data.company_expenses_amount))}
        ${metric("Санжар расходы", formatMoney((data.departments || [])[0]?.expenses_amount || 0))}
        ${metric("Рауфаль расходы", formatMoney((data.departments || [])[1]?.expenses_amount || 0))}
        ${metric("Статус", data.closing?.status || "Не закрыт")}
      </div>
    </div>
  `;
}


function emptyAdminDashboard(month) {
  return {
    month,
    company_plan_amount: 0,
    company_fact_income_amount: 0,
    company_completion_percent: 0,
    company_remaining_to_plan: 0,
    company_expenses_amount: 0,
    departments: [],
    events: [],
    payment_requests: [],
    closing: { is_closed: false },
  };
}

function normalizeAdminDashboardForMonth(data, month) {
  const normalized = { ...(data || emptyAdminDashboard(month)) };
  normalized.month = month;

  const events = Array.isArray(normalized.events) ? normalized.events : [];
  normalized.events = events.filter((event) => eventMonthKey(event) === month);

  const allowedEventIds = new Set(normalized.events.map((event) => Number(event.id)));
  const requests = Array.isArray(normalized.payment_requests) ? normalized.payment_requests : [];
  normalized.payment_requests = requests.filter((request) => (
    !request.event_id || allowedEventIds.has(Number(request.event_id))
  ));

  return normalized;
}

function renderAdminEmptyDashboard(month, error = null) {
  const data = emptyAdminDashboard(month);
  state.adminData = data;
  renderAdminTabs();
  renderSummary([]);

  $("dashboardTitle").textContent = "Админка";
  $("dashboardHint").textContent = error ? `Не удалось загрузить данные за ${month}` : "";

  if (state.activeAdminTab === "requests") {
    $("dashboardContent").innerHTML = renderPaymentRequestsTable([], "Все заявки", "regular");
  } else if (state.activeAdminTab === "requests_archive") {
    $("dashboardContent").innerHTML = renderPaymentRequestsTable([], "Архив заявок", "archive");
  } else if (state.activeAdminTab === "plans") {
    $("dashboardContent").innerHTML = renderPlansSkeleton(data);
  } else if (state.activeAdminTab === "closing") {
    $("dashboardContent").innerHTML = renderClosingSkeleton(data);
  } else {
    $("dashboardContent").innerHTML = `
      <div class="empty-state">
        Данных за выбранный период нет.
      </div>
    `;
  }

  attachPaymentRequestActions();
  attachFilters();
  attachEventRows();
  attachPlansModal();
}

function clearDashboardForPeriodLoading() {
  if ($("dashboardContent")) {
    $("dashboardContent").innerHTML = `
      <div class="empty-state">Загружаем выбранный период…</div>
    `;
  }
}


function renderAdminDashboard(data) {
  data = normalizeAdminDashboardForMonth(data, state.month);
  state.adminData = data;
  renderAdminTabs();

  renderSummary([]);

  $("dashboardTitle").textContent = "Админка";
  $("dashboardHint").textContent = "";

  if (state.activeAdminTab === "overview") {
    $("dashboardContent").innerHTML = renderAdminOverview(data);
  } else if (state.activeAdminTab === "events") {
    $("dashboardContent").innerHTML = renderAdminEvents(data);
  } else if (state.activeAdminTab === "requests") {
    $("dashboardContent").innerHTML = renderPaymentRequestsTable(data.payment_requests || [], "Все заявки", "regular");
  } else if (state.activeAdminTab === "requests_archive") {
    $("dashboardContent").innerHTML = renderPaymentRequestsTable(data.payment_requests || [], "Архив заявок", "archive");
  } else if (state.activeAdminTab === "plans") {
    $("dashboardContent").innerHTML = renderPlansSkeleton(data);
  } else if (state.activeAdminTab === "closing") {
    $("dashboardContent").innerHTML = renderClosingSkeleton(data);
  }

  attachPaymentRequestActions();
  attachFilters();
  attachEventRows();
  attachPlansModal();
}

function renderDepartmentDashboard(data, paymentRequests = []) {
  $("adminTabs").classList.add("hidden");
  renderSummary([
    ["План отдела", formatMoney(data.plan_amount)],
    ["Факт", formatMoney(data.fact_income_amount)],
    ["Выполнение", `${data.completion_percent}%`],
    ["Расходы", formatMoney(data.expenses_amount)],
  ]);

  $("dashboardTitle").textContent = `Кабинет отдела: ${data.department_name}`;
  $("dashboardHint").textContent = data.include_drafts ? "С черновиками" : "Без черновиков";

  const requests = data.payment_requests || paymentRequests || [];

  $("dashboardContent").innerHTML = `
    <div class="grid cards">
      ${metric("Остаток до плана", formatMoney(data.remaining_to_plan))}
      ${metric("Мероприятий", data.events_count)}
      ${metric("Черновиков", data.drafts_count)}
      ${metric("Менеджеров", data.managers?.length || data.managers_count || 0)}
    </div>
    <div class="block-title"><h3>Мероприятия</h3></div>
    ${renderEventsTable(data.events || [], true)}
    ${renderPaymentRequestsTable(requests, "Заявки отдела")}
  `;

  attachPaymentRequestActions();
  attachFilters();
  attachEventRows();
}



function renderManagerTopActions(data) {
  return `
    <div class="manager-top-actions">
      <button class="secondary" id="managerCreateEventShortcut">+ Создать мероприятие</button>
    </div>
  `;
}

function renderManagerPlanPanel(data) {
  const plan = asNumber(data.personal_plan_amount);
  const fact = asNumber(data.fact_income_amount);
  const percent = plan > 0 ? Math.round((fact / plan) * 10000) / 100 : 0;
  const remaining = Math.max(0, plan - fact);
  const monthLabel = MONTHS_RU.find(([m]) => m === state.month.slice(5, 7))?.[1] || state.month;

  return `
    <section class="manager-plan-panel">
      <div>
        <div class="overview-label">Цель на месяц</div>
        <h3>${monthLabel} ${state.month.slice(0, 4)}</h3>
      </div>
      <div class="manager-plan-main">
        <div class="manager-plan-row">
          <strong>Факт: ${formatMoney(fact)} ₸</strong>
          <strong>Цель: ${formatMoney(plan)} ₸</strong>
          <strong>${percent}%</strong>
        </div>
        ${progressLine(percent)}
        <div class="muted">Осталось: ${formatMoney(remaining)} ₸ · мероприятий: ${data.events_count || 0}</div>
      </div>
    </section>
  `;
}



function getManagerDashboardEvent(eventId) {
  return (state.managerData?.events || []).find((event) => Number(event.id) === Number(eventId)) || null;
}

function refreshManagerMiniCardSelection() {
  document.querySelectorAll("[data-manager-event-id]").forEach((card) => {
    const isOpen = Number(card.getAttribute("data-manager-event-id")) === Number(state.selectedManagerEventId);
    card.classList.toggle("is-open", isOpen);
  });
}


function fitMiniBadgeText(el, minFont = 7.5, maxFont = 12) {
  if (!el) return;

  el.style.fontSize = `${maxFont}px`;
  el.style.letterSpacing = "";
  el.style.transform = "";
  el.style.transformOrigin = "left center";
  el.style.width = "";
  el.style.textOverflow = "clip";

  const available = el.clientWidth;
  if (!available || available <= 0) return;

  let size = maxFont;
  while (size > minFont && el.scrollWidth > available + 1) {
    size -= 0.5;
    el.style.fontSize = `${size}px`;
  }

  if (el.scrollWidth > available + 1) {
    const scale = Math.max(0.72, Math.min(1, available / el.scrollWidth));
    el.style.transform = `scaleX(${scale})`;
    el.style.width = `${100 / scale}%`;
  }
}

function fitMiniCardBadges(card = null) {
  const scope = card || document;
  scope.querySelectorAll(".manager-mini-card .mini-pill").forEach((el) => fitMiniBadgeText(el, 7, 12));
  scope.querySelectorAll(".manager-mini-card .mini-badge-row .status-badge").forEach((el) => fitMiniBadgeText(el, 7, 12));
  scope.querySelectorAll(".manager-mini-card .mini-badge-row .coauthor-badge").forEach((el) => fitMiniBadgeText(el, 6.8, 12));
}

function scheduleMiniBadgeFit(card = null) {
  requestAnimationFrame(() => fitMiniCardBadges(card));
}


function updateCurrentManagerMiniCardLive() {
  try {
    if (!state.selectedManagerEventId || !state.currentManagerEvent) return;

    const card = document.querySelector(`[data-manager-event-id="${state.selectedManagerEventId}"]`);
    if (!card) return;

    const items = getDraftItems(state.selectedManagerEventId);
    const summary = calculateDraftSummaryPreview(items, state.currentManagerEvent, state.currentManagerSummary);
    const miniSummary = applyEventShareToSummaryValues(summary, state.currentManagerEvent);
    state.currentManagerSummary = summary;

    const titleEl = card.querySelector("[data-mini-title]");
    const metaEl = card.querySelector("[data-mini-meta]");
    const calcEl = card.querySelector("[data-mini-calc]");
    const statusEl = card.querySelector("[data-mini-status]");
    let coauthorEl = card.querySelector("[data-mini-coauthor]");
    const pills = card.querySelectorAll(".mini-pill");
    const budgetPill = pills[0];
    const incomePill = pills[1];

    if (titleEl) titleEl.textContent = state.currentManagerEvent.client_name || "Без заказчика";
    if (metaEl) metaEl.textContent = `${state.currentManagerEvent.title || "Без названия"} · ${formatDateRu(state.currentManagerEvent.event_date)}`;
    if (calcEl) calcEl.textContent = customerPaymentLabel(state.currentManagerEvent.client_calc_type);
    if (statusEl) {
      statusEl.textContent = statusLabel(state.currentManagerEvent.status);
      statusEl.className = `status-badge ${eventStatusToneClass(state.currentManagerEvent.status)}`;
    }

    if (eventIsCoauthored(state.currentManagerEvent)) {
      if (!coauthorEl) {
        const badgeRow = card.querySelector(".mini-badge-row") || card;
        badgeRow.insertAdjacentHTML("beforeend", coauthorBadgeHtml(state.currentManagerEvent, "data-mini-coauthor"));
        coauthorEl = card.querySelector("[data-mini-coauthor]");
      } else {
        const name = state.currentManagerEvent.coauthor_name || state.currentManagerEvent.owner_manager_name || "менеджер";
        coauthorEl.textContent = `Соавтор: ${name}`;
      }
    } else if (coauthorEl) {
      coauthorEl.remove();
    }

    if (budgetPill) budgetPill.innerHTML = `<strong>Бюджет:</strong> ${formatMoney(summary.external_total || 0)}`;
    if (incomePill) incomePill.innerHTML = `<strong>Доход:</strong> ${formatMoney(miniSummary.final_company_income || 0)}`;

    card.setAttribute("data-event-status", state.currentManagerEvent.status || "");
    card.classList.remove("status-tone-draft", "status-tone-review", "status-tone-accepted");
    card.classList.add(eventStatusToneClass(state.currentManagerEvent.status));

    scheduleMiniBadgeFit(card);

    const dashboardEvent = getManagerDashboardEvent(state.selectedManagerEventId);
    if (dashboardEvent) {
      dashboardEvent.title = state.currentManagerEvent.title;
      dashboardEvent.client_name = state.currentManagerEvent.client_name;
      dashboardEvent.event_date = state.currentManagerEvent.event_date;
      dashboardEvent.client_calc_type = state.currentManagerEvent.client_calc_type;
      dashboardEvent.status = state.currentManagerEvent.status;
      dashboardEvent.external_total = summary.external_total || 0;
      dashboardEvent.final_company_income = miniSummary.final_company_income || 0;
      dashboardEvent.manager_salary = miniSummary.manager_salary || 0;
      dashboardEvent.is_coauthored = state.currentManagerEvent.is_coauthored;
      dashboardEvent.coauthor_name = state.currentManagerEvent.coauthor_name;
      dashboardEvent.coauthor_user_id = state.currentManagerEvent.coauthor_user_id;
      dashboardEvent.share_percent = state.currentManagerEvent.share_percent;
    }
  } catch (error) {
    console.warn("Mini card live update skipped:", error);
  }
}

function renderManagerEventList(data) {
  const events = data.events || [];
  const monthLabel = MONTHS_RU.find(([m]) => m === state.month.slice(5, 7))?.[1] || state.month.slice(5, 7);
  const periodLabel = `${monthLabel} ${state.month.slice(0, 4)}`;

  return `
    <aside class="manager-sidebar-card">
      <h3>Мероприятия</h3>
      <p class="muted">Проекты за ${periodLabel}</p>

      <div class="manager-mini-list">
        ${events.length ? events.map((event) => `
          <button class="manager-mini-card ${eventStatusToneClass(event.status)} ${Number(state.selectedManagerEventId) === Number(event.id) ? "is-open" : ""}" data-manager-event-id="${event.id}" data-event-status="${event.status}">
            <div class="mini-card-pills">
              ${managerCardMetric("Бюджет", formatMoney(event.external_total || 0))}
              ${managerCardMetric("Доход", formatMoney(event.final_company_income || 0))}
            </div>
            <strong data-mini-title>${event.client_name || "Без заказчика"}</strong>
            <span data-mini-meta>${event.title || "Без названия"} · ${formatDateRu(event.event_date)}</span>
            <small data-mini-calc>${customerPaymentLabel(event.client_calc_type)}</small>
            <div class="mini-badge-row">
              <em data-mini-status class="status-badge ${eventStatusToneClass(event.status)}">${statusLabel(event.status)}</em>
              ${coauthorBadgeHtml(event, 'data-mini-coauthor')}
            </div>
          </button>
        `).join("") : `<div class="empty-state">Мероприятий за ${periodLabel} нет.</div>`}
      </div>
    </aside>
  `;
}

async function renderManagerEventDetail(eventId, options = {}) {
  const holder = document.getElementById("managerEventDetail");
  if (!holder) return;

  if (eventId) {
    state.selectedManagerEventId = Number(eventId);
    refreshManagerMiniCardSelection();
  }

  if (!eventId) {
    holder.innerHTML = `
      <div class="manager-empty-detail">
        <div class="empty-icon">▦</div>
        <h3>Выбери мероприятие</h3>
        <p class="muted">Создай новое или открой черновик слева.</p>
      </div>
    `;
    return;
  }

  if (!options.noLoading) {
    holder.innerHTML = `<div class="empty-state">Загрузка мероприятия...</div>`;
  }

  try {
    const [event, items, summary] = options.useDraft && state.currentManagerEvent
      ? [state.currentManagerEvent, state.currentManagerItems || [], state.currentManagerSummary]
      : await Promise.all([
          api(`/events/${eventId}`),
          api(`/events/${eventId}/items`),
          api(`/events/${eventId}/summary`),
        ]);

    await refreshManagerPaymentRequestsForEvent(eventId);

    const dashboardEvent = getManagerDashboardEvent(eventId);
    const draftEvent = getDraftEvent({ ...(event || {}), ...(dashboardEvent || {}) });
    state.currentManagerEvent = draftEvent;
    const draftItems = getDraftItems(eventId, items || []);
    const previewSummary = calculateDraftSummaryPreview(draftItems, draftEvent, summary);
    state.currentManagerSummary = previewSummary;
    state.currentManagerItems = draftItems;

    holder.innerHTML = renderManagerEventCard(draftEvent, draftItems, previewSummary);
    attachManagerCreateWorkspaceActions();
    attachDraftEventInputs(eventId);
    attachDraftInputs(eventId);
  } catch (error) {
    holder.innerHTML = `<div class="error">${error.message}</div>`;
  }
}


function externalRowAmount(item) {
  return asNumber(item.external_price) * asNumber(item.external_quantity || 1) * asNumber(item.external_days || 1);
}

function externalItemsTotal(items) {
  return (items || [])
    .filter((item) => item.item_type !== "manager_salary")
    .reduce((sum, item) => sum + externalRowAmount(item), 0);
}

function externalAgencyCommissionAmount(items, event) {
  const percent = asNumber(event?.agency_commission_amount);
  return Math.round(externalItemsTotal(items) * percent / 100);
}

function externalClientVatAmount(items, event) {
  if (event?.client_calc_type !== "ip_contrast_event") return 0;
  return Math.round((externalItemsTotal(items) + externalAgencyCommissionAmount(items, event)) * 0.16);
}

function externalSimplifiedMarkupAmount(items, event) {
  if (event?.client_calc_type !== "simplified") return 0;
  return Math.round((externalItemsTotal(items) + externalAgencyCommissionAmount(items, event)) * asNumber(event?.simplified_bank_tax_percent) / 100);
}

function externalTotalToPay(items, event) {
  return externalItemsTotal(items)
    + externalAgencyCommissionAmount(items, event)
    + externalClientVatAmount(items, event)
    + externalSimplifiedMarkupAmount(items, event);
}



function eventSharePercent(event) {
  const value = asNumber(event?.share_percent || 100);
  if (!Number.isFinite(value) || value <= 0) return 100;
  return Math.min(100, value);
}

function eventIsCoauthored(event) {
  return Boolean(event?.is_coauthored) || eventSharePercent(event) < 100 || Boolean(event?.coauthor_name);
}

function applyEventShareToSummaryValues(summary, event) {
  const share = eventSharePercent(event);
  if (!eventIsCoauthored(event) || share >= 100) return summary;

  return {
    ...summary,
    manager_salary: Math.round(asNumber(summary.manager_salary) * share / 100),
    final_company_income: Math.round(asNumber(summary.final_company_income) * share / 100),
    share_percent: share,
  };
}

function coauthorBadgeHtml(event, attrs = "") {
  if (!eventIsCoauthored(event)) return "";
  const name = event?.coauthor_name || event?.owner_manager_name || "менеджер";
  return `<span class="coauthor-badge" title="Соавтор: ${name}" ${attrs}>Соавтор: ${name}</span>`;
}


function calculateDraftSummaryPreview(items, event, backendSummary = null) {
  const shown = (items || []).filter((item) => item.item_type !== "manager_salary");
  const regular = shown.filter((item) => item.item_type !== "coordinator");
  const coordinators = shown.filter((item) => item.item_type === "coordinator");

  const regularExternal = regular.reduce((sum, item) => sum + externalRowAmount(item), 0);
  const regularFact = regular.reduce((sum, item) => {
    const fact = item.amount_fact === null || item.amount_fact === undefined || item.amount_fact === ""
      ? externalRowAmount(item)
      : asNumber(item.amount_fact);
    return sum + fact;
  }, 0);

  const coordinatorExternal = coordinators.reduce((sum, item) => sum + externalRowAmount(item), 0);
  const coordinatorCompanyShare = Math.round(coordinatorExternal * 0.5);

  const itemsTotal = shown.reduce((sum, item) => sum + externalRowAmount(item), 0);
  const agency = externalAgencyCommissionAmount(shown, event);
  const clientBase = itemsTotal + agency;
  const clientVat = event?.client_calc_type === "ip_contrast_event" ? Math.round(clientBase * 0.16) : 0;
  const simplifiedMarkup = event?.client_calc_type === "simplified"
    ? Math.round(clientBase * asNumber(event?.simplified_bank_tax_percent) / 100)
    : 0;
  const turnover = clientBase + clientVat + simplifiedMarkup;

  const contractorVatCredit = regular.reduce((sum, item) => sum + internalVatValue(item), 0);
  const deductions = regular.reduce((sum, item) => sum + internalDeductionValue(item), 0);

  const taxRate = event?.client_calc_type === "ip_contrast_event" || event?.client_calc_type === "our_no_vat"
    ? 12
    : (event?.client_calc_type === "simplified" ? 5 : 0);
  const taxBase = event?.client_calc_type === "simplified" ? turnover : clientBase;
  const taxes = Math.round(taxBase * taxRate / 100);
  const taxesNet = taxes - deductions;

  const vatNet = Math.max(0, clientVat - contractorVatCredit);

  const regularCommission = regularExternal - regularFact;
  const managerBase = regularCommission + agency + simplifiedMarkup + contractorVatCredit + deductions - taxes;
  const managerSalary = managerBase > 0 ? Math.round(managerBase * asNumber(event?.manager_percent || 21) / 100) : 0;
  const companyIncome = managerBase - managerSalary + coordinatorCompanyShare;

  const preview = {
    ...(backendSummary || {}),
    turnover_with_vat: turnover,
    external_total: turnover,
    agency_commission_amount: agency,
    client_vat_amount: clientVat,
    contractor_vat_credit: contractorVatCredit,
    deductions_total: deductions,
    taxes_total: taxes,
    taxes_net: taxesNet,
    tax_base_amount: taxBase,
    vat_to_pay: vatNet,
    vat_net: vatNet,
    regular_positions_commission: regularCommission,
    total_commission_amount: regularCommission + agency,
    manager_salary: managerSalary,
    coordinator_company_share: coordinatorCompanyShare,
    final_company_income: companyIncome,
    tax_rate_percent: taxRate,
    simplified_bank_tax_amount: simplifiedMarkup,
  };

  return preview;
}



function summaryNumber(summary, key) {
  return asNumber(summary?.[key]);
}

function internalAgencyCommissionAmount(items, event, summary) {
  return summaryNumber(summary, "agency_commission_amount") || externalAgencyCommissionAmount(items, event);
}

function internalSimplifiedMarkupAmount(items, event, summary) {
  return summaryNumber(summary, "simplified_bank_tax_amount") || externalSimplifiedMarkupAmount(items, event);
}

function internalTaxesNet(summary) {
  return summaryNumber(summary, "taxes_net") || (summaryNumber(summary, "taxes_total") - summaryNumber(summary, "deductions_total"));
}

function internalVatNet(summary) {
  return summaryNumber(summary, "vat_net") || summaryNumber(summary, "vat_to_pay") || summaryNumber(summary, "vat_total");
}

function draftKeyForEvent(eventId) {
  return String(eventId || state.selectedManagerEventId || "");
}

function cloneItem(item) {
  return JSON.parse(JSON.stringify(item));
}

function ensureCoordinator(items) {
  const existing = (items || []).find((item) => item.item_type === "coordinator");
  if (existing) return items;

  return [{
    id: `tmp-coordinator-${Date.now()}`,
    is_temp: true,
    item_type: "coordinator",
    external_name: "Координатор",
    external_price: 0,
    external_quantity: 1,
    external_days: 1,
    external_amount: 0,
    external_note: "",
    amount_fact: null,
    paid_amount: 0,
    payment_method: null,
    iin_bin: null,
    iin_bin_locked: false,
    tax_check_status: null,
    vat_amount: 0,
    deduction_amount: 0,
    internal_note: null,
    sort_order: -100,
  }, ...(items || [])];
}

function getDraftItems(eventId, sourceItems = null) {
  const key = draftKeyForEvent(eventId);
  if (!state.managerDraftItemsByEventId) state.managerDraftItemsByEventId = {};
  if (!state.managerDraftDeletedByEventId) state.managerDraftDeletedByEventId = {};
  if (!state.managerDraftItemsByEventId[key]) {
    state.managerDraftItemsByEventId[key] = ensureCoordinator(sourceItems || []).map(cloneItem);
  }
  return state.managerDraftItemsByEventId[key];
}

function getDraftDeletedIds(eventId) {
  const key = draftKeyForEvent(eventId);
  if (!state.managerDraftDeletedByEventId) state.managerDraftDeletedByEventId = {};
  if (!state.managerDraftDeletedByEventId[key]) state.managerDraftDeletedByEventId[key] = [];
  return state.managerDraftDeletedByEventId[key];
}

function setDraftItemValue(eventId, itemId, field, value) {
  const items = getDraftItems(eventId);
  const item = items.find((candidate) => String(candidate.id) === String(itemId));
  if (!item) return;

  if (field === "payment_method" && itemPaymentMethodLocked(item)) {
    return;
  }

  if (field === "iin_bin" && itemHasActiveInvoicePaymentRequest(item)) {
    return;
  }

  if (["external_price", "external_quantity", "external_days", "amount_fact"].includes(field)) {
    item[field] = value === "" ? null : Math.round(normalizeNumberInput(value));
  } else {
    item[field] = value;
  }

  if (field === "payment_method") {
    if (value !== "invoice") {
      item.iin_bin = null;
      item.iin_bin_locked = false;
      item.tax_check_status = null;
    }

    if (value === "cash" || value === "card" || value === "") {
      item.vat_amount = 0;
      item.deduction_amount = 0;
    }

    if (value === "self_employed") {
      ensureSelfEmployedItemTax(item);
    }
  }

  if (["external_price", "external_quantity", "external_days"].includes(field) && item.item_type === "coordinator") {
    item.amount_fact = Math.round(externalRowAmount(item) * 0.5);
  }

  if (field === "amount_fact" && (item.payment_method === "self_employed" || item.tax_check_status === "self_employed")) {
    ensureSelfEmployedItemTax(item);
  }

  if (["amount_fact", "external_price", "external_quantity", "external_days"].includes(field)) {
    recalculateCheckedItemTax(item);
  }
  updateCurrentManagerMiniCardLive();
}


function attachDraftEventInputs(eventId) {
  document.querySelectorAll("[data-event-field]").forEach((input) => {
    input.addEventListener("input", () => {
      setDraftEventValue(eventId, input.getAttribute("data-event-field"), input.value);
      refreshDraftVisibleCalculations(eventId);
      updateCurrentManagerMiniCardLive();
    });

    input.addEventListener("change", () => {
      setDraftEventValue(eventId, input.getAttribute("data-event-field"), input.value);
      renderManagerEventDetail(eventId, { useDraft: true, noLoading: true });
    });
  });
}

async function saveDraftEvent(eventId) {
  const draftEvent = state.managerDraftEventsById?.[String(eventId)] || state.currentManagerEvent;
  if (!draftEvent) return;

  const savedEvent = await api(`/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify({
      client_name: draftEvent.client_name,
      title: draftEvent.title,
      event_date: eventDateForInput(draftEvent.event_date),
      department_id: draftEvent.department_id,
      manager_id: draftEvent.manager_id,
      status: draftEvent.status,
      client_calc_type: draftEvent.client_calc_type,
      manager_percent: draftEvent.manager_percent,
      agency_commission_amount: draftEvent.agency_commission_amount,
      agency_commission_spread_enabled: draftEvent.agency_commission_spread_enabled,
      simplified_bank_tax_percent: draftEvent.client_calc_type === "simplified" ? draftEvent.simplified_bank_tax_percent : 0,
    }),
  });

  if (savedEvent) {
    state.currentManagerEvent = { ...state.currentManagerEvent, ...savedEvent };
    state.managerDraftEventsById[String(eventId)] = { ...state.currentManagerEvent };
  }
}


function taxBaseForItem(item) {
  const fact = asNumber(item.amount_fact);
  return fact > 0 ? fact : externalRowAmount(item);
}

function recalculateCheckedItemTax(item) {
  if (!item || item.payment_method !== "invoice" || !item.tax_check_status || ["not_found", "error"].includes(item.tax_check_status)) {
    return;
  }

  const base = taxBaseForItem(item);

  if (item.tax_check_status === "our_vat") {
    const withoutVat = Math.round(base / 1.16);
    item.vat_amount = Math.round(base - withoutVat);
    item.deduction_amount = Math.round(withoutVat * 0.10);
    return;
  }

  if (item.tax_check_status === "our_no_vat") {
    item.vat_amount = 0;
    item.deduction_amount = Math.round(base * 0.10);
    return;
  }

  item.vat_amount = 0;
  item.deduction_amount = 0;
}

function updateInternalRowCells(itemId) {
  const items = getDraftItems(state.selectedManagerEventId);
  const item = items.find((candidate) => String(candidate.id) === String(itemId));
  const row = document.querySelector(`tr[data-event-item-row="${itemId}"]`);
  if (!item || !row) return;

  ensureSelfEmployedItemTax(item);

  const vatCell = row.querySelector(".vat-col strong");
  const deductionCell = row.querySelector(".deduction-col strong");
  const commissionCell = row.querySelector(".commission-col strong");
  const paidCell = row.querySelector(".paid-col strong");

  if (vatCell) vatCell.textContent = formatMoney(internalVatValue(item));
  if (deductionCell) deductionCell.textContent = formatMoney(internalDeductionValue(item));
  if (commissionCell) commissionCell.textContent = formatMoney(internalCommissionValue(item));
  if (paidCell) paidCell.textContent = formatMoney(item.paid_amount);

  const paymentSelect = row.querySelector(`[data-item-field="payment_method"][data-item-id="${itemId}"]`);
  const activeMethod = paymentMethodFromActiveRequest(item);
  if (paymentSelect) {
    paymentSelect.value = activeMethod || item.payment_method || "";
    paymentSelect.disabled = itemPaymentMethodLocked(item);
  }

  const binInput = row.querySelector(`[data-item-field="iin_bin"][data-item-id="${itemId}"]`);
  if (binInput) {
    binInput.value = item.iin_bin || "";
    binInput.disabled = Boolean(item.iin_bin_locked || itemHasActiveInvoicePaymentRequest(item));
  }

  const oldCheckButton = row.querySelector(`[data-check-tax-item="${itemId}"]`);
  const oldUnlockButton = row.querySelector(`[data-unlock-tax-item="${itemId}"]`);
  const oldButton = oldCheckButton || oldUnlockButton;
  if (oldButton) {
    const lockedByRequest = itemHasActiveInvoicePaymentRequest(item);
    oldButton.outerHTML = item.iin_bin_locked
      ? `<button class="icon-btn" data-unlock-tax-item="${itemId}" title="${lockedByRequest ? "BIN закреплён активной заявкой" : "Изменить BIN"}" ${lockedByRequest ? "disabled" : ""}>✎</button>`
      : `<button class="icon-btn ${isTaxProblem(item) ? "danger" : ""}" data-check-tax-item="${itemId}" title="Проверить КГД">✓</button>`;
  }

  row.classList.toggle("tax-problem-row", isTaxProblem(item));
  bindTaxButtons();
}

function updateInternalSummaryCards() {
  const items = getDraftItems(state.selectedManagerEventId);
  const summary = calculateDraftSummaryPreview(items, state.currentManagerEvent, state.currentManagerSummary);
  state.currentManagerSummary = summary;
  updateCurrentManagerMiniCardLive();

  const grid = document.querySelector(".manager-summary-grid-six");
  if (!grid) return;

  const values = [
    ["Оборот", formatMoney(summary.turnover_with_vat ?? summary.external_total)],
    ["Комиссия", formatMoney(summary.agency_commission_amount ?? 0)],
    ["Менеджер", formatMoney(summary.manager_salary)],
    [`Налоги ${summary.tax_rate_percent || 0}%`, formatMoney(internalTaxesNet(summary))],
    ["НДС", formatMoney(internalVatNet(summary))],
    ["Доход компании", formatMoney(summary.final_company_income)],
  ];

  const cards = Array.from(grid.querySelectorAll(".metric"));
  values.forEach(([label, value], index) => {
    const card = cards[index];
    if (!card) return;
    const labelEl = card.querySelector(".label");
    const valueEl = card.querySelector(".value");
    if (labelEl) labelEl.textContent = label;
    if (valueEl) valueEl.textContent = value;
  });
}

function updateTaxUiInPlace(itemId) {
  updateInternalRowCells(itemId);
  updateInternalSummaryCards();
  updateCurrentManagerMiniCardLive();
}



function showDraftSavedHint() {
  let hint = document.getElementById("draftSavedHint");
  const head = document.querySelector(".manager-event-actions");
  if (!head) return;

  if (!hint) {
    hint = document.createElement("span");
    hint.id = "draftSavedHint";
    hint.style.marginLeft = "10px";
    hint.style.fontSize = "13px";
    hint.style.fontWeight = "700";
    hint.style.color = "#3d7f00";
    head.appendChild(hint);
  }

  hint.textContent = "Сохранено";
  window.clearTimeout(showDraftSavedHint._timer);
  showDraftSavedHint._timer = window.setTimeout(() => {
    hint.textContent = "";
  }, 1500);
}


function attachDraftInputs(eventId) {
  document.querySelectorAll("[data-item-field]").forEach((input) => {
    input.addEventListener("input", () => {
      const itemId = input.getAttribute("data-item-id");
      const field = input.getAttribute("data-item-field");
      setDraftItemValue(eventId, itemId, field, input.value);
      refreshDraftVisibleCalculations(eventId);
      updateTaxUiInPlace(itemId);
    });

    input.addEventListener("change", () => {
      const itemId = input.getAttribute("data-item-id");
      const field = input.getAttribute("data-item-field");
      setDraftItemValue(eventId, itemId, field, input.value);

      if (["external_price", "amount_fact"].includes(field)) {
        const items = getDraftItems(eventId);
        const item = items.find((candidate) => String(candidate.id) === String(itemId));
        input.value = field === "amount_fact" ? internalFactDisplayValue(item) : formatInputNumber(item?.external_price);
      }

      if (["external_quantity", "external_days"].includes(field)) {
        const items = getDraftItems(eventId);
        const item = items.find((candidate) => String(candidate.id) === String(itemId));
        input.value = integerInputValue(item?.[field], "1");
      }

      if (field === "payment_method") {
        syncDraftItemFromRowBeforeTax(itemId);
        rerenderCurrentManagerCard();
      } else {
        refreshDraftVisibleCalculations(eventId);
        updateTaxUiInPlace(itemId);
      }
    });
  });
}

function refreshDraftVisibleCalculations(eventId) {
  const items = getDraftItems(eventId);
  const summary = calculateDraftSummaryPreview(items, state.currentManagerEvent, state.currentManagerSummary);
  state.currentManagerSummary = summary;

  const activeTab = state.managerEstimateTab || "external";
  if (activeTab === "internal") {
    const grid = document.querySelector(".manager-summary-grid-six");
    if (grid) {
      grid.innerHTML = `
        ${metric("Оборот", formatMoney(summary.turnover_with_vat ?? summary.external_total))}
        ${metric("Комиссия", formatMoney(summary.agency_commission_amount ?? 0))}
        ${metric("Менеджер", formatMoney(summary.manager_salary))}
        ${metric(`Налоги ${summary.tax_rate_percent || 0}%`, formatMoney(internalTaxesNet(summary)))}
        ${metric("НДС", formatMoney(internalVatNet(summary)))}
        <div class="card metric income-metric">
          <div class="label">Доход компании</div>
          <div class="value">${formatMoney(summary.final_company_income)}</div>
        </div>
      `;
    }
  }

  document.querySelectorAll("[data-event-item-row]").forEach((row) => {
    const itemId = row.getAttribute("data-event-item-row");
    const item = items.find((candidate) => String(candidate.id) === String(itemId));
    if (!item) return;

    const sumCell = row.querySelector("[data-row-sum]");
    if (sumCell) sumCell.textContent = formatMoney(externalRowAmount(item));

    const deductionCell = row.querySelector(".deduction-col strong");
    if (deductionCell) deductionCell.textContent = formatMoney(internalDeductionValue(item));

    const vatCell = row.querySelector(".vat-col strong");
    if (vatCell) vatCell.textContent = formatMoney(internalVatValue(item));

    const commissionCell = row.querySelector(".commission-col strong");
    if (commissionCell) commissionCell.textContent = formatMoney(internalCommissionValue(item));
  });
  updateCurrentManagerMiniCardLive();
}

function internalCommissionValue(item) {
  const fact = item.amount_fact === null || item.amount_fact === undefined ? 0 : asNumber(item.amount_fact);
  return externalRowAmount(item) - fact;
}

function internalDeductionValue(item) {
  if (item.payment_method === "self_employed") {
    const base = asNumber(item.amount_fact) > 0 ? asNumber(item.amount_fact) : externalRowAmount(item);
    return Math.round(base * 0.10);
  }
  if (item.payment_method === "invoice") return asNumber(item.deduction_amount);
  return 0;
}

function internalVatValue(item) {
  if (item.payment_method === "invoice") return asNumber(item.vat_amount);
  return 0;
}


function isReviewManagerEvent(event) {
  return event?.status === "review";
}


function eventStatusToneClass(status) {
  const normalized = String(status || "").toLowerCase();

  if (["review", "on_review", "pending", "pending_review"].includes(normalized)) return "status-tone-review";
  if (["accepted", "approved", "completed", "done", "archive", "archived"].includes(normalized)) return "status-tone-accepted";
  if (["revision", "needs_revision", "rework"].includes(normalized)) return "status-tone-draft";
  return "status-tone-draft";
}

function canEditManagerEvent(event) {
  return ["draft", "revision"].includes(event?.status);
}

function canShowDeleteManagerEvent(event) {
  return ["draft", "revision", "review"].includes(event?.status);
}

function canDeleteManagerEvent(event) {
  return ["draft", "revision"].includes(event?.status);
}

function isActiveMiniCard(event) {
  return String(event?.id) === String(state.selectedManagerEventId);
}


function isCoordinatorItem(item) {
  return item.item_type === "coordinator";
}
function taxStatusLabel(status) {
  const map = {
    our_vat: "ОУР с НДС",
    our_no_vat: "ОУР без НДС",
    simplified: "Упрощенка",
    snr: "СНР",
    self_employed: "Самозанятый",
    not_found: "Не найдено",
    error: "Ошибка",
  };
  return map[status] || status || "";
}

function isTaxProblem(item) {
  return item.payment_method === "invoice" && ["not_found", "error"].includes(item.tax_check_status);
}



function rowInput(value, attrs = "") {
  return `<input ${attrs} value="${value ?? ""}" />`;
}

function estimateInputMoney(value) {
  if (value === null || value === undefined || value === "") return "";
  return formatMoney(value);
}

function internalFactDisplayValue(item) {
  if (item.item_type === "coordinator") {
    return formatMoney(Math.round(externalRowAmount(item) * 0.5));
  }
  return formatInputNumber(item.amount_fact);
}


function draggableHandle(item) {
  if (item.item_type === "coordinator") return `<span class="drag-handle muted" title="Координатор всегда первый">⋮⋮</span>`;
  return `<span class="drag-handle" draggable="true" data-drag-item="${item.id}" title="Перетащить строку">⋮⋮</span>`;
}

function addDraftRegularPosition(eventId) {
  const items = getDraftItems(eventId);
  items.push({
    id: `tmp-${state.managerDraftTempSeq++}`,
    is_temp: true,
    item_type: "regular",
    external_name: "",
    external_price: 0,
    external_quantity: 1,
    external_days: 1,
    external_amount: 0,
    external_note: "",
    amount_fact: null,
    paid_amount: 0,
    payment_method: null,
    iin_bin: null,
    iin_bin_locked: false,
    tax_check_status: null,
    vat_amount: 0,
    deduction_amount: 0,
    internal_note: null,
    sort_order: items.length,
  });
}

function moveDraftItem(eventId, fromId, toId) {
  if (!fromId || !toId || String(fromId) === String(toId)) return;
  const items = getDraftItems(eventId);
  const fromIndex = items.findIndex((item) => String(item.id) === String(fromId));
  const toIndex = items.findIndex((item) => String(item.id) === String(toId));
  if (fromIndex < 0 || toIndex < 0) return;

  const moving = items[fromIndex];
  const target = items[toIndex];
  if (moving.item_type === "coordinator" || target.item_type === "coordinator") return;

  items.splice(fromIndex, 1);
  const newToIndex = items.findIndex((item) => String(item.id) === String(toId));
  items.splice(newToIndex, 0, moving);

  items.forEach((item, index) => {
    item.sort_order = item.item_type === "coordinator" ? -100 : index;
  });
}

function tableFocusableCells() {
  return Array.from(document.querySelectorAll(".estimate-table input:not(:disabled), .estimate-table select:not(:disabled), .estimate-table textarea:not(:disabled)"));
}

function focusTableCell(current, direction) {
  const cells = tableFocusableCells();
  const index = cells.indexOf(current);
  if (index < 0) return false;

  const row = current.closest("tr");
  const rows = Array.from(current.closest("tbody")?.querySelectorAll("tr[data-event-item-row]") || []);
  const rowIndex = rows.indexOf(row);
  const cellIndex = Array.from(row?.querySelectorAll("input:not(:disabled), select:not(:disabled), textarea:not(:disabled)") || []).indexOf(current);

  if (direction === "right") {
    const next = cells[index + 1];
    if (next) next.focus();
    return Boolean(next);
  }

  if (direction === "left") {
    const prev = cells[index - 1];
    if (prev) prev.focus();
    return Boolean(prev);
  }

  if (direction === "down" || direction === "enter") {
    const nextRow = rows[rowIndex + 1];
    if (nextRow) {
      const rowCells = Array.from(nextRow.querySelectorAll("input:not(:disabled), select:not(:disabled), textarea:not(:disabled)"));
      const target = rowCells[Math.min(cellIndex, rowCells.length - 1)] || rowCells[0];
      if (target) target.focus();
      return Boolean(target);
    }

    if (direction === "enter") {
      addDraftRegularPosition(state.selectedManagerEventId);
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
      setTimeout(() => {
        const freshRows = Array.from(document.querySelectorAll("tr[data-event-item-row]"));
        const lastRow = freshRows[freshRows.length - 1];
        const firstCell = lastRow?.querySelector("input:not(:disabled), select:not(:disabled), textarea:not(:disabled)");
        if (firstCell) firstCell.focus();
      }, 0);
      return true;
    }

    return false;
  }

  if (direction === "up") {
    const prevRow = rows[rowIndex - 1];
    if (prevRow) {
      const rowCells = Array.from(prevRow.querySelectorAll("input:not(:disabled), select:not(:disabled), textarea:not(:disabled)"));
      const target = rowCells[Math.min(cellIndex, rowCells.length - 1)] || rowCells[0];
      if (target) target.focus();
      return Boolean(target);
    }
    return false;
  }

  return false;
}

function attachEstimateKeyboardNavigation() {
  document.querySelectorAll(".estimate-table input, .estimate-table select, .estimate-table textarea").forEach((field) => {
    field.addEventListener("keydown", (event) => {
      if (event.key === "ArrowRight") {
        event.preventDefault();
        focusTableCell(field, "right");
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        focusTableCell(field, "left");
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        focusTableCell(field, "down");
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        focusTableCell(field, "up");
      } else if (event.key === "Enter") {
        event.preventDefault();
        focusTableCell(field, "enter");
      }
    });
  });
}

function attachEstimateDragAndDrop() {
  document.querySelectorAll("[data-drag-item]").forEach((handle) => {
    handle.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", handle.getAttribute("data-drag-item"));
      event.dataTransfer.effectAllowed = "move";
      handle.closest("tr")?.classList.add("dragging-row");
    });

    handle.addEventListener("dragend", () => {
      handle.closest("tr")?.classList.remove("dragging-row");
    });
  });

  document.querySelectorAll("tr[data-event-item-row]").forEach((row) => {
    row.addEventListener("dragover", (event) => {
      event.preventDefault();
      row.classList.add("drag-over-row");
    });

    row.addEventListener("dragleave", () => {
      row.classList.remove("drag-over-row");
    });

    row.addEventListener("drop", (event) => {
      event.preventDefault();
      row.classList.remove("drag-over-row");
      const fromId = event.dataTransfer.getData("text/plain");
      const toId = row.getAttribute("data-event-item-row");
      moveDraftItem(state.selectedManagerEventId, fromId, toId);
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });
}


function renderExternalEstimate(items, eventId, event = null) {
  const shownItems = sortItemsCoordinatorFirst(items || []).filter((item) => item.item_type !== "manager_salary");
  const total = externalItemsTotal(shownItems);
  const agency = externalAgencyCommissionAmount(shownItems, event);
  const vat = externalClientVatAmount(shownItems, event);
  const simplifiedMarkup = externalSimplifiedMarkupAmount(shownItems, event);
  const totalToPay = externalTotalToPay(shownItems, event);

  return `
    <div class="manager-add-position-row">
      <button class="secondary" id="addExternalPositionBtn">+ Добавить позицию</button>
    </div>

    <div class="table-wrap estimate-table-wrap">
      <table class="estimate-table external-estimate-table">
        <thead>
          <tr>
            <th class="drag-col"></th>
            <th>Позиция</th>
            <th>Цена</th>
            <th>Кол-во</th>
            <th>Дни</th>
            <th>Сумма</th>
            <th>Примечание</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${shownItems.map((item) => `
            <tr data-event-item-row="${item.id}" class="${isTaxProblem(item) ? "tax-problem-row" : ""}">
              <td class="drag-col">${draggableHandle(item)}</td>
              <td>${rowInput(item.external_name || "", `placeholder="Новая позиция" data-item-field="external_name" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(formatInputNumber(item.external_price), `data-item-field="external_price" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(integerInputValue(item.external_quantity, "1"), `data-item-field="external_quantity" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(integerInputValue(item.external_days, "1"), `data-item-field="external_days" data-item-id="${item.id}"`)}</td>
              <td><strong data-row-sum>${formatMoney(externalRowAmount(item))}</strong></td>
              <td>${rowInput(item.external_note || "", `placeholder="Примечание для клиента" data-item-field="external_note" data-item-id="${item.id}"`)}</td>
              <td>${deleteButtonHtmlForItem(item)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>

    <div class="external-estimate-totals external-estimate-totals-four">
      ${metric("Итого по позициям", formatMoney(total))}
      ${metric(`Комиссия агентства ${asNumber(event?.agency_commission_amount)}%`, formatMoney(agency))}
      ${event?.client_calc_type === "simplified"
        ? metric(`Банк+налоги ${formatPlainNumber(event?.simplified_bank_tax_percent)}%`, formatMoney(simplifiedMarkup))
        : metric(event?.client_calc_type === "ip_contrast_event" ? "НДС 16%" : "НДС", formatMoney(vat))}
      <div class="card metric income-metric">
        <div class="label">Итого к оплате</div>
        <div class="value">${formatMoney(totalToPay)}</div>
      </div>
    </div>
  `;
}

function renderInternalEstimate(items, event, summary = null) {
  const shownItems = sortItemsCoordinatorFirst(items || []).filter((item) => item.item_type !== "manager_salary");
  const agency = internalAgencyCommissionAmount(shownItems, event, summary);
  const simplifiedMarkup = internalSimplifiedMarkupAmount(shownItems, event, summary);
  const managerSalary = summaryNumber(summary, "manager_salary");

  return `
    <div class="manager-add-position-row">
      <button class="secondary" id="addInternalPositionBtn">+ Добавить позицию</button>
    </div>

    <div class="table-wrap estimate-table-wrap">
      <table class="estimate-table internal-estimate-table">
        <thead>
          <tr>
            <th class="drag-col"></th>
            <th>Позиция</th>
            <th>Смета</th>
            <th>Факт</th>
            <th>Оплата</th>
            <th>БИН/ИИН</th>
            <th>КГД</th>
            <th>НДС</th>
            <th>Вычеты</th>
            <th>Комиссия</th>
            <th>Оплачено</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${shownItems.map((item) => {
            ensureSelfEmployedItemTax(item);
            const activeMethod = paymentMethodFromActiveRequest(item);
            const effectivePaymentMethod = activeMethod || item.payment_method;
            const paymentLocked = itemPaymentMethodLocked(item);
            const invoiceLockedByRequest = itemHasActiveInvoicePaymentRequest(item);
            const binDisabled = isCoordinatorItem(item) || effectivePaymentMethod !== "invoice";
            return `
              <tr data-event-item-row="${item.id}" class="${isTaxProblem(item) ? "tax-problem-row" : ""}">
                <td class="drag-col">${draggableHandle(item)}</td>
                <td>${rowInput(item.external_name || "", `placeholder="Новая позиция" data-item-field="external_name" data-item-id="${item.id}"`)}</td>
                <td><strong>${formatMoney(externalRowAmount(item))}</strong></td>
                <td>${rowInput(internalFactDisplayValue(item), `data-item-field="amount_fact" data-item-id="${item.id}" ${item.item_type === "coordinator" ? "disabled" : ""}`)}</td>
                <td>
                  ${isCoordinatorItem(item) ? `
                    <select disabled>
                      <option selected>—</option>
                    </select>
                  ` : `
                    <select data-item-field="payment_method" data-item-id="${item.id}" ${paymentLocked ? "disabled" : ""}>
                      <option value="" ${!effectivePaymentMethod ? "selected" : ""}>—</option>
                      <option value="cash" ${effectivePaymentMethod === "cash" ? "selected" : ""}>Налик</option>
                      <option value="card" ${effectivePaymentMethod === "card" ? "selected" : ""}>На карту</option>
                      <option value="self_employed" ${effectivePaymentMethod === "self_employed" ? "selected" : ""}>Самозанятый</option>
                      <option value="invoice" ${effectivePaymentMethod === "invoice" ? "selected" : ""}>По счету</option>
                    </select>
                  `}
                </td>
                <td>${rowInput(binDisabled ? "" : (item.iin_bin || ""), `placeholder="12 цифр" class="${isTaxProblem(item) ? "tax-problem-input" : ""}" ${binDisabled ? "disabled" : `data-item-field="iin_bin" data-item-id="${item.id}" ${(item.iin_bin_locked || invoiceLockedByRequest) ? "disabled" : ""}`}`)}</td>
                <td>
                  ${isCoordinatorItem(item) ? "—" : (effectivePaymentMethod === "invoice" ? `
                    ${item.iin_bin_locked ? `
                      <button class="icon-btn" data-unlock-tax-item="${item.id}" title="${invoiceLockedByRequest ? "BIN закреплён активной заявкой" : "Изменить BIN"}" ${invoiceLockedByRequest ? "disabled" : ""}>✎</button>
                    ` : `
                      <button class="icon-btn ${isTaxProblem(item) ? "danger" : ""}" data-check-tax-item="${item.id}" title="Проверить КГД">✓</button>
                    `}
                  ` : "—")}
                </td>
                <td class="vat-col"><strong>${formatMoney(internalVatValue(item))}</strong></td>
                <td class="deduction-col"><strong>${formatMoney(internalDeductionValue(item))}</strong></td>
                <td class="commission-col"><strong>${formatMoney(internalCommissionValue(item))}</strong></td>
                <td class="paid-col"><strong>${formatMoney(item.paid_amount)}</strong></td>
                <td>${deleteButtonHtmlForItem(item)}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderManagerEventCard(event, items = [], summary = null) {
  const canEdit = canEditManagerEvent(event);
  const canDelete = canDeleteManagerEvent(event);
  const eventDeleteLocked = eventHasActivePaymentRequests(event);
  const eventDeleteAllowed = canDelete && !eventDeleteLocked;
  const eventDeleteTitle = eventDeleteDisabledReason(event);
  const isReadonlyReview = event?.status === "review";
  const readonlyAttrs = canEdit ? "" : "disabled";


  const activeTab = state.managerEstimateTab || "external";

  return `
    <section class="manager-event-card ${isReadonlyReview ? "is-readonly" : ""}" style="${isReadonlyReview ? "background: rgba(115,120,130,.045);" : ""}">
      <div class="manager-event-head">
        <div>
          <div class="overview-label">Карточка мероприятия</div>
          <h2>${event.title}</h2>
          <div class="event-badge-row">
            <span class="status ${event.status} ${eventStatusToneClass(event.status)}">${statusLabel(event.status)}</span>
            ${coauthorBadgeHtml(event)}
          </div>
        </div>
        <div class="inline-actions">
          <button class="secondary" data-manager-event-pay="${event.id}">Оплатить</button>
          <button class="ghost" data-manager-event-payments="${event.id}">Мои оплаты</button>
          <button class="ghost" data-manager-event-transfer="${event.id}">Передать</button>
          ${eventIsCoauthored(event)
            ? `<button class="ghost" data-manager-event-remove-coauthor="${event.id}">Удалить соавтора</button>`
            : `<button class="ghost" data-manager-event-coauthor="${event.id}">Соавтор</button>`}
          <button class="danger-btn" data-manager-event-delete="${event.id}" title="${eventDeleteTitle}" ${eventDeleteAllowed ? "" : "disabled"} style="margin-left:auto;">Удалить</button>
        </div>
      </div>

      ${isReadonlyReview ? `<div class="readonly-banner" style="margin: 12px 0 0; padding: 10px 12px; border: 1px solid rgba(50,168,82,.35); background: rgba(50,168,82,.10); color:#256b31; border-radius:12px; font-size:13px; font-weight:700;">Мероприятие на проверке — смета и поля недоступны для редактирования. Можно делать оплаты, передавать мероприятие и добавлять соавтора.</div>` : ""}

      <div class="manager-event-fields" style="${isReadonlyReview ? "filter: grayscale(.35); opacity:.72;" : ""}">
        <label>Тип расчёта с заказчиком
          <select data-event-field="client_calc_type" data-event-id="${event.id}" ${readonlyAttrs}>
            <option value="ip_contrast_event" ${event.client_calc_type === "ip_contrast_event" ? "selected" : ""}>ИП Contrast Event</option>
            <option value="our_no_vat" ${event.client_calc_type === "our_no_vat" ? "selected" : ""}>ОУР без НДС</option>
            <option value="simplified" ${event.client_calc_type === "simplified" ? "selected" : ""}>Упрощенка</option>
            <option value="cash" ${event.client_calc_type === "cash" ? "selected" : ""}>Нал</option>
          </select>
        </label>
        <label>Дата мероприятия
          <input type="date" value="${eventDateForInput(event.event_date)}" data-event-field="event_date" data-event-id="${event.id}" ${readonlyAttrs} />
        </label>
        <label>Название заказчика
          <input value="${event.client_name || ""}" data-event-field="client_name" data-event-id="${event.id}" ${readonlyAttrs} />
        </label>
        <label>Название мероприятия
          <input value="${event.title || ""}" data-event-field="title" data-event-id="${event.id}" ${readonlyAttrs} />
        </label>
        <label>Комиссия агентства, %
          <input value="${formatPlainNumber(event.agency_commission_amount || 0)}" data-event-field="agency_commission_amount" data-event-id="${event.id}" ${readonlyAttrs} />
        </label>
        ${event.client_calc_type === "simplified" ? `
          <label>Банк+налоги, %
            <input value="${formatPlainNumber(event.simplified_bank_tax_percent || 0)}" data-event-field="simplified_bank_tax_percent" data-event-id="${event.id}" ${readonlyAttrs} />
          </label>
        ` : ""}
      </div>

      <div class="estimate-tabs">
        <button class="${activeTab === "external" ? "tab-btn active" : "ghost"}" data-estimate-tab="external">Внешняя смета</button>
        <button class="${activeTab === "internal" ? "tab-btn active" : "ghost"}" data-estimate-tab="internal">Внутренняя смета</button>
      </div>

      <div id="managerEstimatePanel">
        ${activeTab === "external" ? renderExternalEstimate(items || [], event.id, event) : renderInternalEstimate(items || [], event, summary)}
      </div>

      ${summary && activeTab === "internal" ? `
        <div class="manager-summary-grid manager-summary-grid-six">
          ${metric("Оборот", formatMoney(summary.turnover_with_vat ?? summary.external_total))}
          ${metric("Комиссия", formatMoney(summary.agency_commission_amount ?? 0))}
          ${metric("Менеджер", formatMoney(summary.manager_salary))}
          ${metric(`Налоги ${summary.tax_rate_percent || 0}%`, formatMoney(internalTaxesNet(summary)))}
          ${metric("НДС", formatMoney(internalVatNet(summary)))}
          <div class="card metric income-metric">
            <div class="label">Доход компании</div>
            <div class="value">${formatMoney(summary.final_company_income)}</div>
          </div>
        </div>
      ` : ""}

      <div class="manager-card-bottom-actions">
        <button class="save-draft-btn ${canEdit ? "" : "disabled-action"}" data-manager-event-save-draft="${event.id}" ${readonlyAttrs}>Сохранить черновик</button>
        <button class="${canEdit ? "" : "disabled-action"}" data-manager-event-send-review="${event.id}" ${readonlyAttrs}>Отправить Саше</button>
      </div>
    </section>
  `;
}

function renderManagerCreateModal() {
  return `
    <div class="modal-head">
      <div>
        <div class="overview-label">Новое мероприятие</div>
        <h2>Создать мероприятие</h2>
      </div>
      <button id="managerCreateModalCloseBtn" class="ghost">Закрыть</button>
    </div>

    <div class="form-grid">
      <label>Заказчик
        <input id="newEventClientName" placeholder="Название заказчика" />
      </label>
      <label>Название мероприятия
        <input id="newEventTitle" placeholder="Например: Корпоратив" />
      </label>
      <label>Дата мероприятия
        <input id="newEventDate" type="date" />
      </label>
      <label>Тип расчёта с заказчиком
        <select id="newEventCalcType">
          <option value="ip_contrast_event">ИП Contrast Event</option>
          <option value="our_no_vat">ОУР без НДС</option>
          <option value="simplified">Упрощенка</option>
          <option value="cash">Нал</option>
        </select>
      </label>
      <label>Комиссия агентства
        <input id="newEventAgencyCommission" value="0" />
      </label>
      <label>Банк+налоги, % для Упрощенки
        <input id="newEventSimplifiedPercent" value="0" disabled />
      </label>
    </div>

    <div id="managerCreateError" class="error hidden"></div>
    <div class="divider"></div>
    <button id="createManagerEventBtn">Создать мероприятие</button>
  `;
}

function openManagerCreateModal() {
  const title = document.getElementById("plansModalTitle");
  if (title) {
    title.textContent = "Создать мероприятие";
    title.classList.add("manager-create-modal-title");
  }

  const modal = $("plansModalBackdrop");
  modal.classList.add("manager-create-modal");
  modal.classList.remove("hidden");

  $("plansModalContent").innerHTML = renderManagerCreateModal();
  attachManagerCreateForm();
  attachManagerCalcTypeToggle();

  const close = document.getElementById("managerCreateModalCloseBtn");
  if (close) {
    close.addEventListener("click", () => {
      $("plansModalBackdrop").classList.add("hidden");
      $("plansModalBackdrop").classList.remove("manager-create-modal");
    });
  }
}

function renderManagerDashboardLayout(data) {
  return `
    ${renderManagerTopActions(data)}
    ${renderManagerPlanPanel(data)}
    <div class="manager-workspace">
      ${renderManagerEventList(data)}
      <main id="managerEventDetail" class="manager-detail-card">
        <div class="manager-empty-detail">
          <div class="empty-icon">▦</div>
          <h3>Выбери мероприятие</h3>
          <p class="muted">Создай новое или открой черновик слева.</p>
        </div>
      </main>
    </div>
  `;
}

function calcItemTaxFields(paymentMethod, taxStatus, amountFact, externalAmount) {
  const base = asNumber(amountFact) > 0 ? asNumber(amountFact) : asNumber(externalAmount);

  if (paymentMethod === "invoice" && taxStatus === "our_vat") {
    const amountWithoutVat = base / 1.16;
    return {
      vat_amount: Math.round((base - amountWithoutVat) * 100) / 100,
      deduction_amount: Math.round(amountWithoutVat * 0.10 * 100) / 100,
    };
  }

  if (paymentMethod === "invoice" && taxStatus === "our_no_vat") {
    return {
      vat_amount: 0,
      deduction_amount: Math.round(base * 0.10 * 100) / 100,
    };
  }

  if (paymentMethod === "self_employed") {
    return {
      vat_amount: 0,
      deduction_amount: Math.round(base * 0.10 * 100) / 100,
    };
  }

  return { vat_amount: 0, deduction_amount: 0 };
}


function itemPayloadForSave(item) {
  ensureSelfEmployedItemTax(item);
  const isCoordinator = item.item_type === "coordinator";
  const coordinatorFact = Math.round(externalRowAmount(item) * 0.5);

  return {
    item_type: item.item_type || "regular",
    external_name: item.external_name || "",
    external_price: Math.round(asNumber(item.external_price)),
    external_quantity: Math.round(asNumber(item.external_quantity || 1)),
    external_days: Math.round(asNumber(item.external_days || 1)),
    external_note: item.external_note || null,
    amount_fact: isCoordinator ? coordinatorFact : (item.amount_fact === "" || item.amount_fact === undefined || item.amount_fact === null ? null : Math.round(asNumber(item.amount_fact))),
    paid_amount: item.paid_amount || 0,
    payment_method: isCoordinator ? null : (item.payment_method || null),
    iin_bin: isCoordinator || item.payment_method !== "invoice" ? null : (item.iin_bin || null),
    iin_bin_locked: isCoordinator || item.payment_method !== "invoice" ? false : (item.iin_bin_locked || false),
    tax_check_status: isCoordinator
      ? null
      : (item.payment_method === "self_employed" ? "self_employed" : (item.payment_method === "invoice" ? (item.tax_check_status || null) : null)),
    vat_amount: isCoordinator ? 0 : (item.vat_amount || 0),
    deduction_amount: isCoordinator ? 0 : (item.deduction_amount || 0),
    internal_note: item.internal_note || null,
    sort_order: isCoordinator ? -100 : (item.sort_order || 0),
  };
}

async function saveDraftItems(eventId) {
  const items = getDraftItems(eventId);
  items.forEach((item, index) => {
    item.sort_order = item.item_type === "coordinator" ? -100 : index;
  });
  const deletedIds = getDraftDeletedIds(eventId);

  for (const itemId of deletedIds) {
    if (!String(itemId).startsWith("tmp-")) {
      await api(`/event-items/${itemId}`, { method: "DELETE" });
    }
  }

  for (const item of items) {
    const payload = itemPayloadForSave(item);
    if (String(item.id).startsWith("tmp-")) {
      const created = await api(`/events/${eventId}/items`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      item.id = created.id;
      item.is_temp = false;
    } else {
      await api(`/event-items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    }
  }

  // Не очищаем локальный черновик сразу после сохранения, чтобы карточка не мигала.
  // Полная синхронизация с backend произойдёт при следующем открытии карточки.
  state.managerDraftDeletedByEventId[draftKeyForEvent(eventId)] = [];
}

async function addExternalPosition(eventId) {
  addDraftRegularPosition(eventId);
}

function deleteDraftItem(eventId, itemId) {
  const items = getDraftItems(eventId);
  const item = items.find((candidate) => String(candidate.id) === String(itemId));
  if (item?.item_type === "coordinator") {
    alert("Координатора нельзя удалить");
    return;
  }

  if (itemDeleteLockedByPaymentRequest(item)) {
    alert("Нельзя удалить позицию, пока по ней есть активная заявка на оплату. Сначала отмени все заявки по этой позиции.");
    return;
  }

  state.managerDraftItemsByEventId[draftKeyForEvent(eventId)] = items.filter((candidate) => String(candidate.id) !== String(itemId));
  if (!String(itemId).startsWith("tmp-")) {
    getDraftDeletedIds(eventId).push(itemId);
  }
}




function applyManagerCardReadOnly() {
  if (canEditManagerEvent(state.currentManagerEvent)) return;

  const holder = $("managerEventDetail");
  if (!holder) return;

  holder.querySelectorAll(".manager-event-fields input, .manager-event-fields select, .manager-event-fields textarea, .estimate-table input, .estimate-table select, .estimate-table textarea, button[data-check-tax-item], button[data-unlock-tax-item], button[data-delete-item], #addExternalPositionBtn, #addInternalPositionBtn, [data-manager-event-save-draft], [data-manager-event-send-review]").forEach((element) => {
    element.disabled = true;
  });

  holder.querySelectorAll("[data-manager-event-delete]").forEach((element) => {
    element.disabled = true;
  });
}

function bindTaxButtons() {
  document.querySelectorAll("[data-check-tax-item]").forEach((button) => {
    button.onclick = async (event) => {
      event.preventDefault();
      event.stopPropagation();

      if (button.dataset.kgdLoading === "1") return;
      button.dataset.kgdLoading = "1";

      const previousText = button.textContent;
      button.disabled = true;
      button.textContent = "…";
      button.classList.add("is-loading");

      try {
        await checkTaxForItem(button.dataset.checkTaxItem);
      } finally {
        if (button.isConnected) {
          button.disabled = false;
          button.textContent = previousText || "✓";
          button.classList.remove("is-loading");
          delete button.dataset.kgdLoading;
        }
      }
    };
  });

  document.querySelectorAll("[data-unlock-tax-item]").forEach((button) => {
    button.onclick = (event) => {
      event.preventDefault();
      event.stopPropagation();
      unlockTaxForItem(button.dataset.unlockTaxItem);
    };
  });
}


function unlockTaxForItem(itemId) {
  const items = getDraftItems(state.selectedManagerEventId);
  const item = items.find((candidate) => String(candidate.id) === String(itemId));
  if (!item) return;

  if (itemHasActiveInvoicePaymentRequest(item)) {
    alert("БИН нельзя изменить, пока по этой позиции есть активная заявка. Сначала отмени заявку.");
    return;
  }

  item.iin_bin_locked = false;
  item.tax_check_status = null;
  item.vat_amount = 0;
  item.deduction_amount = 0;

  updateTaxUiInPlace(itemId);
}


async function deleteManagerEvent(eventId) {
  if (activePaymentRequestsForEvent(eventId).length > 0) {
    throw new Error("Нельзя удалить мероприятие: есть активные заявки на оплату.");
  }

  await api(`/events/${eventId}`, { method: "DELETE" });
  state.selectedManagerEventId = null;
  state.currentManagerEvent = null;
  await loadDashboard();
  const holder = $("managerEventDetail");
  if (holder) holder.innerHTML = `<div class="empty-state">Мероприятие удалено</div>`;
}

function syncDraftItemFromRowBeforeTax(itemId) {
  const items = getDraftItems(state.selectedManagerEventId);
  const item = items.find((candidate) => String(candidate.id) === String(itemId));
  const row = document.querySelector(`tr[data-event-item-row="${itemId}"]`);

  if (!item || !row) return item || null;

  const paymentSelect = row.querySelector(`[data-item-field="payment_method"][data-item-id="${itemId}"]`);
  const binInput = row.querySelector(`[data-item-field="iin_bin"][data-item-id="${itemId}"]`);
  const factInput = row.querySelector(`[data-item-field="amount_fact"][data-item-id="${itemId}"]`);

  if (paymentSelect && !itemPaymentMethodLocked(item)) item.payment_method = paymentSelect.value || null;
  if (binInput && !itemHasActiveInvoicePaymentRequest(item)) item.iin_bin = binInput.value ? binInput.value.replace(/\D/g, "") : null;
  if (factInput && factInput.value !== "") item.amount_fact = Math.round(normalizeNumberInput(factInput.value));

  if (item.payment_method !== "invoice") {
    item.iin_bin_locked = false;
    item.tax_check_status = null;
    item.vat_amount = 0;
    if (item.payment_method === "self_employed") {
      ensureSelfEmployedItemTax(item);
    } else {
      item.deduction_amount = 0;
    }
  }

  return item;
}

async function checkTaxForItem(itemId) {
  const originalItemId = String(itemId);
  let item = syncDraftItemFromRowBeforeTax(itemId);

  if (!item || item.payment_method !== "invoice") {
    alert("КГД проверка доступна только для способа оплаты “По счету”");
    return;
  }

  const row = document.querySelector(`tr[data-event-item-row="${originalItemId}"]`);
  const input = row?.querySelector(`[data-item-field="iin_bin"][data-item-id="${originalItemId}"]`)
    || document.querySelector(`[data-item-field="iin_bin"][data-item-id="${originalItemId}"]`);

  const iinBin = (input?.value || item.iin_bin || "").trim();

  if (!iinBin) {
    alert("Сначала укажи БИН/ИИН");
    return;
  }

  const normalized = iinBin.replace(/\D/g, "");
  if (normalized.length !== 12) {
    alert("БИН/ИИН должен содержать 12 цифр");
    return;
  }

  item.iin_bin = normalized;
  item.payment_method = "invoice";

  try {
    // Ключевой фикс:
    // КГД должен работать только с настоящим database id.
    // Поэтому сначала сохраняем текущую смету. Если строка была tmp,
    // saveDraftItems() меняет id прямо у этой же ссылки item.
    await saveDraftEvent(state.selectedManagerEventId);
    await saveDraftItems(state.selectedManagerEventId);

    if (String(item.id).startsWith("tmp-")) {
      throw new Error("Не удалось сохранить позицию перед проверкой КГД");
    }

    itemId = item.id;

    const result = await api(`/event-items/${itemId}/tax/check`, {
      method: "POST",
      body: JSON.stringify({ iin_bin: normalized }),
    });

    item.iin_bin = result.iin_bin || normalized;
    item.iin_bin_locked = Boolean(result.iin_bin_locked);
    item.tax_check_status = result.tax_status || result.tax_check_status || null;
    item.vat_amount = Math.round(asNumber(result.vat_amount));
    item.deduction_amount = Math.round(asNumber(result.deduction_amount));
    item.payment_method = "invoice";

    // После сохранения tmp→real id DOM обязан получить новые data-item-id.
    // Поэтому не пытаемся точечно обновлять старую tmp-строку, а перерисовываем карточку.
    rerenderCurrentManagerCard();
    updateCurrentManagerMiniCardLive();
    showDraftSavedHint();
  } catch (error) {
    item.iin_bin = normalized;
    item.iin_bin_locked = false;
    item.tax_check_status = "error";
    item.vat_amount = 0;
    item.deduction_amount = 0;

    if (String(itemId).startsWith("tmp-")) {
      rerenderCurrentManagerCard();
    } else {
      updateTaxUiInPlace(itemId);
    }

    alert(error.message || "КГД не ответил");
  }
}

function rerenderCurrentManagerCard() {
  if (!state.selectedManagerEventId || !state.currentManagerEvent) return;
  const holder = $("managerEventDetail");
  if (!holder) return;

  const items = getDraftItems(state.selectedManagerEventId);
  const summary = calculateDraftSummaryPreview(items, state.currentManagerEvent, state.currentManagerSummary);
  state.currentManagerSummary = summary;
  state.currentManagerItems = items;

  holder.innerHTML = renderManagerEventCard(state.currentManagerEvent, items, summary);
  attachManagerCreateWorkspaceActions();
  attachDraftEventInputs(state.selectedManagerEventId);
  attachDraftInputs(state.selectedManagerEventId);
}



function managerActionEventById(eventId) {
  const draft = state.managerDraftEventsById?.[String(eventId)];
  if (draft) return draft;
  if (state.currentManagerEvent && Number(state.currentManagerEvent.id) === Number(eventId)) return state.currentManagerEvent;
  return (state.managerData?.events || []).find((event) => Number(event.id) === Number(eventId)) || null;
}

async function getActionManagers() {
  try {
    return await api("/events/action-managers");
  } catch (error) {
    // fallback только для показа списка, если endpoint временно недоступен
    return (state.users || []).filter((user) => user.role === "manager" && user.is_active);
  }
}



function setCoauthorStateForEvent(eventId, managerId, managerName) {
  const patch = {
    is_coauthored: true,
    coauthor_name: managerName || null,
    coauthor_user_id: Number(managerId),
    share_percent: 50,
  };

  const key = String(eventId);

  if (state.currentManagerEvent && Number(state.currentManagerEvent.id) === Number(eventId)) {
    state.currentManagerEvent = { ...state.currentManagerEvent, ...patch };
    state.managerDraftEventsById[key] = { ...(state.managerDraftEventsById[key] || state.currentManagerEvent), ...patch };
  }

  const dashboardEvent = getManagerDashboardEvent(eventId);
  if (dashboardEvent) Object.assign(dashboardEvent, patch);
}


function clearCoauthorStateForEvent(eventId) {
  const patch = {
    is_coauthored: false,
    coauthor_name: null,
    coauthor_user_id: null,
    share_percent: 100,
  };

  const key = String(eventId);

  if (state.currentManagerEvent && Number(state.currentManagerEvent.id) === Number(eventId)) {
    state.currentManagerEvent = { ...state.currentManagerEvent, ...patch };
    state.managerDraftEventsById[key] = { ...(state.managerDraftEventsById[key] || state.currentManagerEvent), ...patch };
  }

  const dashboardEvent = getManagerDashboardEvent(eventId);
  if (dashboardEvent) Object.assign(dashboardEvent, patch);
}


function closeManagerActionDropdown() {
  document.querySelectorAll(".manager-action-dropdown").forEach((node) => node.remove());
  document.querySelectorAll("[data-manager-event-transfer], [data-manager-event-coauthor]").forEach((button) => {
    button.classList.remove("action-open");
  });
}

function renderManagerActionDropdown(eventId, action, managers) {
  const event = managerActionEventById(eventId);
  const title = action === "transfer" ? "Передать" : "Соавтор";
  const filteredManagers = (managers || [])
    .filter((manager) => Number(manager.id) !== Number(event?.manager_id))
    .sort((a, b) => String(a.name || "").localeCompare(String(b.name || ""), "ru"));

  return `
    <div class="manager-action-dropdown" data-manager-action-dropdown>
      <div class="manager-action-dropdown-head">
        <strong>${title}</strong>
        <button type="button" class="icon-btn" data-manager-action-close>×</button>
      </div>
      ${filteredManagers.length ? `
        <div class="manager-action-dropdown-list">
          ${filteredManagers.map((manager) => `
            <button type="button" class="manager-action-choice" data-manager-action-choice="${manager.id}" data-manager-action="${action}" data-manager-action-event="${eventId}">
              <span class="manager-action-choice-name">${manager.name || "Менеджер"}</span>
              <span class="manager-action-choice-department">${manager.department_name || departmentNameById(manager.department_id) || ""}</span>
            </button>
          `).join("")}
        </div>
      ` : `
        <div class="manager-action-empty">Нет доступных менеджеров</div>
      `}
    </div>
  `;
}

async function openManagerActionDropdown(button, eventId, action) {
  const alreadyOpen = button.classList.contains("action-open");
  closeManagerActionDropdown();
  if (alreadyOpen) return;

  button.classList.add("action-open");

  const wrapper = document.createElement("div");
  wrapper.className = "manager-action-dropdown";
  wrapper.dataset.managerActionDropdown = "1";
  wrapper.innerHTML = `<div class="manager-action-empty">Загружаем менеджеров…</div>`;

  const actionsHost = button.closest(".inline-actions") || button.parentElement;
  actionsHost.style.position = "relative";
  actionsHost.appendChild(wrapper);

  try {
    const managers = await getActionManagers();
    wrapper.outerHTML = renderManagerActionDropdown(eventId, action, managers);

    const dropdown = actionsHost.querySelector("[data-manager-action-dropdown]");
    if (!dropdown) return;

    dropdown.querySelector("[data-manager-action-close]")?.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeManagerActionDropdown();
    });

    dropdown.querySelectorAll("[data-manager-action-choice]").forEach((choice) => {
      choice.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const managerId = Number(choice.getAttribute("data-manager-action-choice"));
        const selectedAction = choice.getAttribute("data-manager-action");
        const selectedEventId = choice.getAttribute("data-manager-action-event");

        await withLoading(async () => {
          if (selectedAction === "transfer") {
            await api(`/events/${selectedEventId}/transfer`, {
              method: "POST",
              body: JSON.stringify({ manager_id: managerId }),
            });
          } else {
            await api(`/events/${selectedEventId}/coauthor`, {
              method: "POST",
              body: JSON.stringify({ manager_id: managerId }),
            });
            const managerName = choice.querySelector(".manager-action-choice-name")?.textContent?.trim() || "";
            setCoauthorStateForEvent(selectedEventId, managerId, managerName);
          }

          closeManagerActionDropdown();
          state.selectedManagerEventId = Number(selectedEventId);
          await loadDashboard();

          if (selectedAction === "coauthor" && Number(state.selectedManagerEventId) === Number(selectedEventId)) {
            const managerName = choice.querySelector(".manager-action-choice-name")?.textContent?.trim() || "";
            setCoauthorStateForEvent(selectedEventId, managerId, managerName);
            await renderManagerEventDetail(selectedEventId, { useDraft: true, noLoading: true });
          }
        }, selectedAction === "transfer" ? "Передаём мероприятие…" : "Добавляем соавтора…");
      });
    });
  } catch (error) {
    wrapper.innerHTML = `<div class="error">${error.message || "Не удалось загрузить менеджеров"}</div>`;
  }
}




function showToast(message) {
  let toast = document.getElementById("appToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "appToast";
    toast.className = "app-toast";
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(window.__cfToastTimer);
  window.__cfToastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
}


function paymentBaseAmountForItem(item) {
  if (!item) return 0;
  const fact = asNumber(item.amount_fact);
  if (fact > 0) return fact;
  return externalRowAmount(item);
}

function paymentRemainingForItem(item) {
  return Math.max(0, Math.round(paymentBaseAmountForItem(item) - asNumber(item?.paid_amount)));
}

function selfEmployedSurnameFromItem(item) {
  const note = String(item?.internal_note || "");
  const match = note.match(/Самозанятый:\s*(.+)$/i);
  if (match && match[1].trim()) return match[1].trim();

  const request = activeSelfEmployedRequestForItem(item);
  const fromRequest = String(
    request?.contractor_name_snapshot ||
    request?.comment ||
    ""
  ).trim();

  return fromRequest;
}




async function refreshManagerPaymentRequestsForEvent(eventId) {
  if (!eventId) return;

  try {
    const requests = await api(`/events/${eventId}/payment-requests`);
    const otherRequests = (state.managerPaymentRequests || []).filter((request) => Number(request.event_id) !== Number(eventId));
    state.managerPaymentRequests = [...(requests || []), ...otherRequests];
  } catch (error) {
    console.warn("Не удалось обновить заявки мероприятия", error);
  }
}


function activePaymentRequestsForItem(item) {
  if (!item || String(item.id).startsWith("tmp-")) return [];
  return (state.managerPaymentRequests || []).filter((request) =>
    Number(request.event_item_id) === Number(item.id) &&
    !["cancelled", "rejected"].includes(request.status)
  );
}


function activeSelfEmployedRequestForItem(item) {
  return activePaymentRequestsForItem(item).find((request) => request.payment_method === "self_employed") || null;
}

function selfEmployedDeductionBase(item) {
  const fact = asNumber(item?.amount_fact);
  if (fact > 0) return fact;
  const external = externalRowAmount(item || {});
  return external > 0 ? external : asNumber(item?.external_amount);
}

function ensureSelfEmployedItemTax(item) {
  if (!item) return item;

  const isSelfEmployed = item.payment_method === "self_employed" || item.tax_check_status === "self_employed" || itemHasActiveSelfEmployedPaymentRequest(item);
  if (!isSelfEmployed) return item;

  item.payment_method = "self_employed";
  item.tax_check_status = "self_employed";
  item.iin_bin = null;
  item.iin_bin_locked = false;
  item.vat_amount = 0;
  item.deduction_amount = Math.round(selfEmployedDeductionBase(item) * 0.10);

  const surname = selfEmployedSurnameFromItem(item);
  if (surname && !String(item.internal_note || "").match(/Самозанятый:\s*/i)) {
    item.internal_note = `Самозанятый: ${surname}`;
  }

  return item;
}


function activePaymentRequestMethodForItem(item) {
  const request = activePaymentRequestsForItem(item)[0];
  return request?.payment_method || null;
}

function itemHasActivePaymentRequest(item) {
  return activePaymentRequestsForItem(item).length > 0;
}

function itemDeleteLockedByPaymentRequest(item) {
  return itemHasActivePaymentRequest(item);
}

function deleteLockTitleForItem(item) {
  return itemDeleteLockedByPaymentRequest(item)
    ? "Есть активные заявки на оплату"
    : "Удалить позицию";
}

function deleteButtonHtmlForItem(item) {
  if (item.item_type === "coordinator") return "";

  const locked = itemDeleteLockedByPaymentRequest(item);
  return `<button class="icon-btn danger" data-delete-item="${item.id}" title="${deleteLockTitleForItem(item)}" ${locked ? "disabled" : ""}>×</button>`;
}

function activePaymentRequestsForEvent(eventId) {
  return (state.managerPaymentRequests || []).filter((request) =>
    Number(request.event_id) === Number(eventId) &&
    !["cancelled", "rejected"].includes(request.status)
  );
}

function eventHasActivePaymentRequests(event) {
  if (!event) return false;
  return activePaymentRequestsForEvent(event.id).length > 0;
}

function eventDeleteDisabledReason(event) {
  return eventHasActivePaymentRequests(event) ? "Есть активные заявки на оплату" : "Удалить мероприятие";
}



function itemHasActiveInvoicePaymentRequest(item) {
  return activePaymentRequestsForItem(item).some((request) => request.payment_method === "invoice");
}

function itemHasActiveSelfEmployedPaymentRequest(item) {
  return activePaymentRequestsForItem(item).some((request) => request.payment_method === "self_employed");
}

function itemPaymentMethodLocked(item) {
  if (!item) return false;
  if (item.item_type === "coordinator" || item.item_type === "manager_salary") return true;
  if (itemHasLockedInvoicePayment(item)) return true;
  return itemHasActivePaymentRequest(item);
}

function paymentMethodFromActiveRequest(item) {
  const method = activePaymentRequestMethodForItem(item);
  return method || null;
}


function itemHasLockedInvoicePayment(item) {
  return Boolean(item?.iin_bin_locked && item?.iin_bin);
}

function itemHasLockedSelfEmployedPayment(item) {
  return Boolean(
    itemHasActiveSelfEmployedPaymentRequest(item) ||
    selfEmployedSurnameFromItem(item)
  );
}

function paymentMethodIsFixed(item) {
  if (!item) return false;
  if (item.is_new_payment_position) return false;
  if (item.item_type === "coordinator" || item.item_type === "manager_salary") return true;
  if (itemHasLockedInvoicePayment(item)) return true;
  if (itemHasActivePaymentRequest(item)) return true;
  if (itemHasLockedSelfEmployedPayment(item)) return true;
  return false;
}

function fixedPaymentMethodForItem(item) {
  if (!item) return null;
  if (item.item_type === "coordinator" || item.item_type === "manager_salary") return "cash";
  const activeMethod = paymentMethodFromActiveRequest(item);
  if (activeMethod) return activeMethod;
  if (itemHasLockedInvoicePayment(item)) return "invoice";
  if (item?.payment_method === "self_employed" || item?.tax_check_status === "self_employed") return "self_employed";
  return null;
}


function paymentPositionsForEvent(eventId) {
  const items = getDraftItems(eventId)
    .filter((item) => !item.is_deleted && item.item_type !== "manager_salary")
    .map((item) => {
      ensureSelfEmployedItemTax(item);
      item.is_manager_salary_virtual = false;
      item.is_new_payment_position = false;
      return item;
    });

  const summary = state.currentManagerSummary || {};
  const managerSalary = Math.round(asNumber(summary.manager_salary || 0));
  const managerPaid = Math.round(asNumber(managerSalaryPaidValue(summary)));

  if (managerSalary > 0) {
    items.push({
      id: "manager_salary",
      event_id: Number(eventId),
      item_type: "manager_salary",
      external_name: "ЗП менеджера",
      external_price: 0,
      external_quantity: 1,
      external_days: 1,
      external_amount: 0,
      amount_fact: managerSalary,
      paid_amount: managerPaid,
      payment_method: "cash",
      internal_note: "Системная позиция ЗП менеджера",
      is_manager_salary_virtual: true,
      is_new_payment_position: false,
    });
  }

  items.push({
    id: "__new_position",
    event_id: Number(eventId),
    item_type: "regular",
    external_name: "+ создать новую позицию",
    external_price: 0,
    external_quantity: 1,
    external_days: 1,
    external_amount: 0,
    amount_fact: null,
    paid_amount: 0,
    payment_method: "cash",
    internal_note: null,
    is_manager_salary_virtual: false,
    is_new_payment_position: true,
  });

  return items;
}

function paymentPositionLabel(item) {
  if (!item) return "";
  if (item.is_new_payment_position) return "+ создать новую позицию";
  const type = item.item_type === "coordinator" ? " · координатор" : (item.item_type === "manager_salary" ? " · ЗП" : "");
  return `${item.external_name || "Позиция"}${type}`;
}

function paymentMethodOptionsForItem(item) {
  const fixed = fixedPaymentMethodForItem(item);
  if (fixed) {
    const labels = {
      invoice: "По счету",
      cash: "Нал",
      card: "На карту",
      self_employed: "Самозанятый",
    };
    return [[fixed, labels[fixed] || fixed]];
  }

  return [
    ["cash", "Нал"],
    ["card", "На карту"],
    ["invoice", "По счету"],
    ["self_employed", "Самозанятый"],
  ];
}

function renderPaymentMethodOptions(item, selected) {
  const options = paymentMethodOptionsForItem(item);
  const fixed = fixedPaymentMethodForItem(item);
  const selectedValue = fixed || selected || item?.payment_method || "cash";
  return options.map(([value, label]) => `
    <option value="${value}" ${selectedValue === value ? "selected" : ""}>${label}</option>
  `).join("");
}

function renderManagerPaymentModal(eventId) {
  const positions = paymentPositionsForEvent(eventId);
  const selectedId = String(positions[0]?.id || "");
  const selected = positions[0] || null;
  const method = selected?.payment_method || "cash";

  return `
    <div class="manager-pay-modal">
      <label>Позиция
        <select id="paymentItemSelect">
          ${positions.map((item) => `
            <option value="${item.id}">${paymentPositionLabel(item)}</option>
          `).join("")}
        </select>
      </label>

      <div id="paymentPositionInfo" class="payment-position-info"></div>

      <label>Сумма заявки
        <input id="paymentAmountInput" inputmode="numeric" value="" placeholder="${formatMoney(paymentRemainingForItem(selected))}" />
      </label>

      <label>Способ оплаты
        <select id="paymentMethodSelect">
          ${renderPaymentMethodOptions(selected, method)}
        </select>
      </label>

      <div id="paymentExtraFields"></div>

      <div class="modal-actions">
        <button class="secondary" id="paymentCreateBtn" type="button">Создать заявку</button>
        <button class="ghost" id="paymentCancelBtn" type="button">Отмена</button>
      </div>
      <div id="paymentMessage" class="muted"></div>
    </div>
  `;
}


function renderNewPaymentPositionFields(item) {
  if (!item?.is_new_payment_position) return "";
  return `
    <label id="paymentNewPositionNameLabel">Название позиции
      <input id="paymentNewPositionNameInput" placeholder="Например: Ведущий" />
    </label>
  `;
}

function newPaymentPositionName() {
  return ($("paymentNewPositionNameInput")?.value || "").trim();
}

function newPaymentPositionAmount() {
  return paymentPayloadAmount();
}

function createDraftItemFromPaymentModal(eventId, method) {
  const name = newPaymentPositionName();
  const amount = newPaymentPositionAmount();

  if (!name) throw new Error("Укажи название новой позиции");
  if (!amount || amount <= 0) throw new Error("Укажи сумму новой позиции");

  const items = getDraftItems(eventId);
  const tempId = `tmp-pay-${Date.now()}`;

  const item = {
    id: tempId,
    event_id: Number(eventId),
    item_type: "regular",
    external_name: name,
    external_price: 0,
    external_quantity: 1,
    external_days: 1,
    external_amount: 0,
    external_note: null,
    amount_fact: amount,
    paid_amount: 0,
    payment_method: method || "cash",
    iin_bin: null,
    iin_bin_locked: false,
    tax_check_status: null,
    vat_amount: 0,
    deduction_amount: 0,
    internal_note: null,
    sort_order: items.length + 1,
    is_deleted: false,
    is_temp: true,
  };

  items.push(item);
  state.managerDraftItemsByEventId[draftKeyForEvent(eventId)] = items;
  return item;
}

async function materializePaymentItemIfNeeded(eventId, item, method) {
  if (!item?.is_new_payment_position) return item;

  const created = createDraftItemFromPaymentModal(eventId, method);
  await persistItemBeforePayment(eventId, created);

  const items = getDraftItems(eventId);
  const materialized = items.find((candidate) => String(candidate.external_name) === String(created.external_name) && !String(candidate.id).startsWith("tmp-")) || created;

  const select = $("paymentItemSelect");
  if (select && materialized?.id) {
    const option = document.createElement("option");
    option.value = String(materialized.id);
    option.textContent = paymentPositionLabel(materialized);
    const newOption = [...select.options].find((candidate) => candidate.value === "__new_position");
    select.insertBefore(option, newOption || null);
    select.value = String(materialized.id);
  }

  return materialized;
}


function selectedPaymentItem(eventId) {
  const select = $("paymentItemSelect");
  const selectedId = select?.value;
  return paymentPositionsForEvent(eventId).find((item) => String(item.id) === String(selectedId)) || null;
}

function renderPaymentPositionState(eventId) {
  const item = selectedPaymentItem(eventId);
  const info = $("paymentPositionInfo");
  const amountInput = $("paymentAmountInput");
  const methodSelect = $("paymentMethodSelect");
  const extra = $("paymentExtraFields");

  if (!item || !info || !amountInput || !methodSelect || !extra) return;

  const base = paymentBaseAmountForItem(item);
  const paid = asNumber(item.paid_amount);
  const remaining = paymentRemainingForItem(item);

  info.innerHTML = `
    ${renderNewPaymentPositionFields(item)}
    <div class="payment-info-grid">
      <div><span>Факт/смета</span><strong>${formatMoney(base)}</strong></div>
      <div><span>Оплачено</span><strong>${formatMoney(paid)}</strong></div>
      <div><span>Остаток</span><strong>${formatMoney(remaining)}</strong></div>
    </div>
    ${paymentMethodIsFixed(item) ? `<div class="payment-extra-hint payment-fixed-hint">Способ оплаты уже закреплён за этой позицией.</div>` : ""}
  `;

  amountInput.value = "";
  amountInput.placeholder = item.is_new_payment_position ? "Сумма новой позиции" : formatMoney(remaining);

  const currentMethod = fixedPaymentMethodForItem(item) || item.payment_method || "cash";
  methodSelect.innerHTML = renderPaymentMethodOptions(item, currentMethod);
  methodSelect.value = currentMethod;
  methodSelect.disabled = paymentMethodIsFixed(item);
  renderPaymentExtraFields(eventId);
}


function formatCardNumberInputValue(value) {
  const digits = String(value || "").replace(/\D/g, "").slice(0, 16);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

function attachPaymentCardFormatting() {
  const input = $("paymentCardInput");
  if (!input) return;

  input.addEventListener("input", () => {
    input.value = formatCardNumberInputValue(input.value);
  });

  input.addEventListener("blur", () => {
    input.value = formatCardNumberInputValue(input.value);
  });
}

function paymentCardDigits() {
  return String($("paymentCardInput")?.value || "").replace(/\D/g, "");
}

function validatePaymentCardBeforeSubmit() {
  const digits = paymentCardDigits();
  if (digits.length !== 16) {
    throw new Error("Для оплаты на карту укажи номер карты из 16 цифр");
  }
  return digits;
}

function invoiceBinAlreadyFixedForPayment(item) {
  return Boolean(
    itemHasLockedInvoicePayment(item) ||
    itemHasActiveInvoicePaymentRequest(item)
  );
}


function renderPaymentExtraFields(eventId) {
  const item = selectedPaymentItem(eventId);
  const method = fixedPaymentMethodForItem(item) || $("paymentMethodSelect")?.value || "cash";
  const extra = $("paymentExtraFields");
  if (!extra || !item) return;

  if (method === "invoice") {
    const isLocked = invoiceBinAlreadyFixedForPayment(item);
    extra.innerHTML = `
      <label>БИН / ИИН
        <div class="payment-bin-row">
          <input id="paymentBinInput" inputmode="numeric" value="${item.iin_bin || ""}" placeholder="12 цифр" ${isLocked ? "disabled" : ""} />
          <button class="ghost payment-check-bin-btn ${isLocked ? "is-disabled" : ""}" id="paymentCheckBinBtn" type="button" ${isLocked ? "disabled aria-disabled=\"true\"" : ""}>Проверить</button>
        </div>
      </label>
      <div class="payment-extra-hint" id="paymentBinHint">${
        isLocked
          ? `БИН уже проверен и закреплён за позицией${item.tax_check_status ? `: ${taxStatusLabel(item.tax_check_status)}` : ""}`
          : "Сначала проверь БИН. После успешной проверки можно создать заявку."
      }</div>
    `;

    $("paymentCheckBinBtn")?.addEventListener("click", async () => {
      const checkBtn = $("paymentCheckBinBtn");
      if (checkBtn?.disabled) return;

      const message = $("paymentMessage");
      if (message) message.textContent = "";

      try {
        setButtonLoading(checkBtn, true, "Проверяем…");
        await checkPaymentInvoiceBin(eventId);
      } catch (error) {
        if (message) message.textContent = error.message || "Не удалось проверить БИН";
      } finally {
        if (checkBtn?.isConnected) setButtonLoading(checkBtn, false);
      }
    });
    return;
  }

  if (method === "card") {
    extra.innerHTML = `
      <label>Номер карты
        <input id="paymentCardInput" inputmode="numeric" placeholder="0000 0000 0000 0000" maxlength="19" />
      </label>
    `;
    attachPaymentCardFormatting();
    return;
  }

  if (method === "self_employed") {
    const surname = selfEmployedSurnameFromItem(item);
    const isLocked = Boolean(surname) && !item.is_new_payment_position;
    extra.innerHTML = `
      <label>Фамилия самозанятого
        <input id="paymentSelfEmployedInput" value="${surname}" placeholder="Фамилия" ${isLocked ? "disabled" : ""} />
      </label>
      <div class="payment-extra-hint">${
        isLocked
          ? "Самозанятый уже закреплён за этой позицией."
          : "Укажи фамилию. КГД не нужен, вычеты 10% запишутся в смету."
      }</div>
    `;
    return;
  }

  extra.innerHTML = "";
}


function paymentItemHasCheckedBin(item) {
  return Boolean(
    item &&
    item.payment_method === "invoice" &&
    item.iin_bin &&
    item.iin_bin_locked &&
    item.tax_check_status &&
    item.tax_check_status !== "not_found"
  );
}

function updatePaymentInvoiceUiAfterCheck(eventId, item) {
  const amountInputBefore = $("paymentAmountInput");
  const amountValue = amountInputBefore?.value || "";

  renderPaymentPositionState(eventId);

  const amountInputAfter = $("paymentAmountInput");
  if (amountInputAfter && amountValue) {
    amountInputAfter.value = amountValue;
  }

  const methodSelect = $("paymentMethodSelect");
  if (methodSelect) {
    methodSelect.value = "invoice";
    methodSelect.disabled = true;
  }

  const binInput = $("paymentBinInput");
  if (binInput) {
    binInput.value = item.iin_bin || "";
    binInput.disabled = true;
  }

  const checkBtn = $("paymentCheckBinBtn");
  if (checkBtn) {
    checkBtn.disabled = true;
    checkBtn.setAttribute("aria-disabled", "true");
    checkBtn.classList.add("is-disabled");
  }

  const message = $("paymentMessage");
  if (message) message.textContent = "БИН проверен и зафиксирован в смете";
}

async function checkPaymentInvoiceBin(eventId) {
  let item = selectedPaymentItem(eventId);
  if (!item || item.item_type === "manager_salary") {
    throw new Error("Выбери позицию из сметы");
  }

  const amountInput = $("paymentAmountInput");
  const amountValueBeforeCheck = amountInput?.value || "";

  item = await materializePaymentItemIfNeeded(eventId, item, "invoice");

  const bin = ($("paymentBinInput")?.value || "").replace(/\D/g, "");
  if (bin.length !== 12) {
    throw new Error("Для оплаты по счету укажи БИН/ИИН из 12 цифр");
  }

  item.payment_method = "invoice";
  item.iin_bin = bin;
  item.iin_bin_locked = false;
  item.tax_check_status = null;

  // Перед КГД сохраняем смету один раз:
  // - для новой позиции это создаёт строку в БД
  // - для существующей позиции это сохраняет актуальный Факт, чтобы вычеты считались от правильной базы
  await persistItemBeforePayment(eventId, item);

  const taxResult = await api(`/event-items/${item.id}/tax/check`, {
    method: "POST",
    body: JSON.stringify({ iin_bin: bin }),
  });

  const checkedStatus = taxResult?.tax_check_status || taxResult?.tax_status;

  if (!taxResult || !checkedStatus || checkedStatus === "not_found") {
    throw new Error(taxResult?.message || "КГД не подтвердил БИН/ИИН");
  }

  item.iin_bin = taxResult.iin_bin || bin;
  item.iin_bin_locked = taxResult.iin_bin_locked === undefined ? true : Boolean(taxResult.iin_bin_locked);
  item.tax_check_status = checkedStatus;
  item.vat_amount = taxResult.vat_amount || 0;
  item.deduction_amount = taxResult.deduction_amount || 0;
  item.payment_method = "invoice";
  item.contractor_name = taxResult.contractor_name || taxResult.name || null;

  // ВАЖНО:
  // второй full-save здесь больше не нужен.
  // /tax/check уже записал iin_bin, iin_bin_locked, tax_check_status, НДС и вычеты в позицию на backend.
  // Повторное saveDraftItems() делало модалку заметно медленнее.

  updateInternalRowCells(item.id);
  updateInternalSummaryCards();
  updateCurrentManagerMiniCardLive();
  updatePaymentInvoiceUiAfterCheck(eventId, item);

  const amountInputAfterCheck = $("paymentAmountInput");
  if (amountInputAfterCheck && amountValueBeforeCheck) {
    amountInputAfterCheck.value = amountValueBeforeCheck;
  }

  return item.contractor_name || `БИН ${bin}`;
}



function formatThousandsInputValue(value) {
  const digits = String(value || "").replace(/\D/g, "");
  if (!digits) return "";
  return Number(digits).toLocaleString("ru-RU").replace(/\u00A0/g, " ");
}

function attachPaymentAmountFormatting() {
  const input = $("paymentAmountInput");
  if (!input) return;

  input.addEventListener("input", () => {
    input.value = formatThousandsInputValue(input.value);
  });

  input.addEventListener("blur", () => {
    input.value = formatThousandsInputValue(input.value);
  });
}


function paymentPayloadAmount() {
  return Math.round(normalizeNumberInput(String($("paymentAmountInput")?.value || "").replace(/\s/g, "")));
}

async function persistItemBeforePayment(eventId, item) {
  await saveDraftEvent(eventId);
  await saveDraftItems(eventId);

  if (String(item.id).startsWith("tmp-")) {
    throw new Error("Не удалось сохранить позицию перед заявкой");
  }
}

async function prepareInvoicePaymentItem(eventId, item) {
  if (!paymentItemHasCheckedBin(item)) {
    throw new Error("Сначала проверь БИН. После успешной проверки можно создать заявку.");
  }

  item.payment_method = "invoice";
  await persistItemBeforePayment(eventId, item);

  return item.contractor_name || item.contractor_name_snapshot || item.internal_note || `БИН ${item.iin_bin}`;
}

async function prepareSelfEmployedPaymentItem(eventId, item) {
  item = await materializePaymentItemIfNeeded(eventId, item, "self_employed");

  const existingSurname = selfEmployedSurnameFromItem(item);
  const surname = existingSurname || (($("paymentSelfEmployedInput")?.value || "").trim());

  if (!surname) {
    throw new Error("Для самозанятого обязательно укажи фамилию");
  }

  item.payment_method = "self_employed";
  item.iin_bin = null;
  item.iin_bin_locked = false;
  item.tax_check_status = "self_employed";
  item.vat_amount = 0;
  item.deduction_amount = Math.round(selfEmployedDeductionBase(item) * 0.10);
  item.internal_note = `Самозанятый: ${surname}`;

  await persistItemBeforePayment(eventId, item);

  updateInternalRowCells(item.id);
  updateInternalSummaryCards();
  updateCurrentManagerMiniCardLive();

  return surname;
}

async function prepareSimplePaymentItem(eventId, item, method) {
  item = await materializePaymentItemIfNeeded(eventId, item, method);

  const fixed = fixedPaymentMethodForItem(item);
  const finalMethod = fixed || method;

  item.payment_method = finalMethod;

  if (finalMethod === "cash" || finalMethod === "card") {
    item.iin_bin = null;
    item.iin_bin_locked = false;
    item.tax_check_status = null;
    item.vat_amount = 0;
    item.deduction_amount = 0;
  }

  await persistItemBeforePayment(eventId, item);
  return item;
}

async function submitManagerPayment(eventId) {
  const message = $("paymentMessage");
  const button = $("paymentCreateBtn");
  if (message) message.textContent = "";

  let item = selectedPaymentItem(eventId);
  if (!item) throw new Error("Выбери позицию");

  const method = fixedPaymentMethodForItem(item) || $("paymentMethodSelect")?.value || "cash";
  const amount = paymentPayloadAmount();

  if (!amount || amount <= 0) {
    throw new Error("Сумма заявки должна быть больше 0");
  }

  if (method === "card") {
    validatePaymentCardBeforeSubmit();
  }

  await withLoading(async () => {
    setButtonLoading(button, true, "Создаём…");

    try {
      if (item.item_type === "manager_salary") {
        if (!["cash", "card"].includes(method)) {
          throw new Error("ЗП менеджера можно оформить только налом или на карту");
        }

        const card = method === "card" ? validatePaymentCardBeforeSubmit() : null;

        await api(`/events/${eventId}/manager-salary/payment-requests`, {
          method: "POST",
          body: JSON.stringify({
            amount_requested: amount,
            payment_method: method,
            card_number: card,
            comment: "ЗП менеджера",
          }),
        });
      } else {
        let comment = null;

        if (method === "invoice") {
          comment = await prepareInvoicePaymentItem(eventId, item);
        } else if (method === "self_employed") {
          comment = await prepareSelfEmployedPaymentItem(eventId, item);
          item = selectedPaymentItem(eventId) || item;
        } else {
          item = await prepareSimplePaymentItem(eventId, item, method);
        }

        const card = method === "card" ? validatePaymentCardBeforeSubmit() : null;

        if (item?.is_new_payment_position || String(item.id).startsWith("tmp-")) {
          throw new Error("Не удалось создать позицию перед заявкой");
        }

        const createdRequest = await api(`/event-items/${item.id}/payment-requests`, {
          method: "POST",
          body: JSON.stringify({
            amount_requested: amount,
            payment_method: method,
            card_number: card,
            comment,
          }),
        });

        state.managerPaymentRequests = [createdRequest, ...(state.managerPaymentRequests || [])];
        updateInternalRowCells(item.id);
        updateInternalSummaryCards();
      }

      $("eventModalBackdrop")?.classList.add("hidden");
      $("eventModalBackdrop")?.classList.remove("payment-modal-mode");
      showToast("Заявка отправлена");
      await loadDashboard();
      if (Number(state.selectedManagerEventId) === Number(eventId)) {
        await renderManagerEventDetail(eventId);
      }
    } finally {
      setButtonLoading(button, false);
    }
  }, "Создаём заявку…");
}

function openManagerPaymentModal(eventId) {
  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

  backdrop.classList.remove("pin-modal-mode");
  backdrop.classList.remove("profile-modal-mode");
  backdrop.classList.add("payment-modal-mode");
  backdrop.classList.remove("hidden");

  title.textContent = "Оплатить";
  content.innerHTML = renderManagerPaymentModal(eventId);

  renderPaymentPositionState(eventId);
  attachPaymentAmountFormatting();

  $("paymentItemSelect")?.addEventListener("change", () => {
    renderPaymentPositionState(eventId);
    attachPaymentAmountFormatting();
  });
  $("paymentMethodSelect")?.addEventListener("change", () => renderPaymentExtraFields(eventId));
  $("paymentCancelBtn")?.addEventListener("click", () => {
    backdrop.classList.add("hidden");
    backdrop.classList.remove("payment-modal-mode");
  });
  $("paymentCreateBtn")?.addEventListener("click", async () => {
    try {
      await submitManagerPayment(eventId);
    } catch (error) {
      const message = $("paymentMessage");
      if (message) message.textContent = error.message || "Не удалось создать заявку";
    }
  });
}


function attachManagerCreateWorkspaceActions() {
  applyManagerCardReadOnly();
  const managerCardCanEdit = canEditManagerEvent(state.currentManagerEvent);

  document.querySelectorAll("[data-estimate-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.managerEstimateTab = button.getAttribute("data-estimate-tab");
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });

  const addExternalBtn = document.getElementById("addExternalPositionBtn");
  const addInternalBtn = document.getElementById("addInternalPositionBtn");
  [addExternalBtn, addInternalBtn].filter(Boolean).forEach((button) => {
    button.addEventListener("click", () => {
      if (!managerCardCanEdit) return;
      addDraftRegularPosition(state.selectedManagerEventId);
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });

  document.querySelectorAll("[data-delete-item]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.disabled) return;
      if (!managerCardCanEdit) return;
      if (!confirm("Удалить позицию?")) return;
      deleteDraftItem(state.selectedManagerEventId, button.getAttribute("data-delete-item"));
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });
document.querySelectorAll("[data-manager-event-save-draft]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!managerCardCanEdit) return;
      const eventId = button.getAttribute("data-manager-event-save-draft");
      await withLoading(async () => {
        await saveDraftEvent(eventId);
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "draft");
        showDraftSavedHint();
        await loadDashboard();
      }, "Сохраняем черновик…");
    });
  });

  document.querySelectorAll("[data-manager-event-send-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!managerCardCanEdit) return;
      const eventId = button.getAttribute("data-manager-event-send-review");
      if (!confirm("Отправить мероприятие Саше на проверку?")) return;

      await withLoading(async () => {
        await saveDraftEvent(eventId);
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "review");
        showDraftSavedHint();
        await loadDashboard();
      }, "Отправляем на проверку…");
    });
  });


attachEstimateKeyboardNavigation();
  attachEstimateDragAndDrop();

  document.querySelectorAll("[data-manager-event-pay]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openManagerPaymentModal(button.getAttribute("data-manager-event-pay"));
    });
  });

  document.querySelectorAll("[data-manager-event-payments]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      await openManagerPaymentRequestsModal(button.getAttribute("data-manager-event-payments"));
    });
  });

  document.querySelectorAll("[data-manager-event-transfer]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openManagerActionDropdown(button, button.getAttribute("data-manager-event-transfer"), "transfer");
    });
  });

  document.querySelectorAll("[data-manager-event-coauthor]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      openManagerActionDropdown(button, button.getAttribute("data-manager-event-coauthor"), "coauthor");
    });
  });

  document.querySelectorAll("[data-manager-event-remove-coauthor]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      const eventId = button.getAttribute("data-manager-event-remove-coauthor");
      if (!confirm("Удалить соавтора? Мероприятие полностью перейдёт тебе.")) return;

      await withLoading(async () => {
        await api(`/events/${eventId}/coauthor/remove`, { method: "POST" });
        closeManagerActionDropdown();
        clearCoauthorStateForEvent(eventId);
        state.selectedManagerEventId = Number(eventId);
        await loadDashboard();

        if (Number(state.selectedManagerEventId) === Number(eventId)) {
          clearCoauthorStateForEvent(eventId);
          await renderManagerEventDetail(eventId, { useDraft: true, noLoading: true });
        }
      }, "Удаляем соавтора…");
    });
  });

  document.querySelectorAll("[data-manager-event-delete]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (button.disabled) return;
      if (!managerCardCanEdit) return;

      const eventId = button.getAttribute("data-manager-event-delete");
      if (eventHasActivePaymentRequests({ id: eventId })) {
        alert("Нельзя удалить мероприятие: есть активные заявки на оплату.");
        return;
      }

      if (!confirm("Удалить мероприятие?")) return;

      await withLoading(async () => {
        await deleteManagerEvent(eventId);
      }, "Удаляем мероприятие…");
    });
  });

  bindTaxButtons();

}


function attachManagerCalcTypeToggle() {
  const calcType = document.getElementById("newEventCalcType");
  const simplifiedInput = document.getElementById("newEventSimplifiedPercent");
  if (!calcType || !simplifiedInput) return;

  const sync = () => {
    const isSimplified = calcType.value === "simplified";
    simplifiedInput.disabled = !isSimplified;
    if (!isSimplified) simplifiedInput.value = "0";
  };

  calcType.addEventListener("change", sync);
  sync();
}

function attachManagerCreateForm() {
  const createBtn = document.getElementById("createManagerEventBtn");
  if (!createBtn) return;

  createBtn.addEventListener("click", async () => {
    const errorBox = document.getElementById("managerCreateError");
    if (errorBox) {
      errorBox.classList.add("hidden");
      errorBox.textContent = "";
    }

    const clientName = document.getElementById("newEventClientName").value.trim();
    const title = document.getElementById("newEventTitle").value.trim();
    const eventDate = document.getElementById("newEventDate").value;
    const calcType = document.getElementById("newEventCalcType").value;
    const agencyCommission = normalizeNumberInput(document.getElementById("newEventAgencyCommission").value);
    const simplifiedPercent = normalizeNumberInput(document.getElementById("newEventSimplifiedPercent").value);

    if (!clientName || !title || !eventDate) {
      if (errorBox) {
        errorBox.textContent = "Заполни заказчика, название и дату.";
        errorBox.classList.remove("hidden");
      } else {
        alert("Заполни заказчика, название и дату");
      }
      return;
    }

    createBtn.disabled = true;

    try {
      await withLoading(async () => {
        const user = state.bootstrap.user;

        const event = await api("/events", {
          method: "POST",
          body: JSON.stringify({
            client_name: clientName,
            title,
            event_date: eventDate,
            department_id: user.department_id,
            manager_id: user.id,
            client_calc_type: calcType,
            manager_percent: 21,
            agency_commission_amount: agencyCommission,
            agency_commission_spread_enabled: false,
            simplified_bank_tax_percent: calcType === "simplified" ? simplifiedPercent : 0,
          }),
        });

        state.selectedManagerEventId = event.id;
        if (eventDate && eventDate.length >= 7) {
          state.month = eventDate.slice(0, 7);
          const globalMonth = document.getElementById("monthSelect");
          const globalYear = document.getElementById("yearSelect");
          if (globalMonth) globalMonth.value = state.month.slice(5, 7);
          if (globalYear) globalYear.value = state.month.slice(0, 4);
        }

        $("plansModalBackdrop").classList.add("hidden");
        $("plansModalBackdrop").classList.remove("manager-create-modal");
        await loadDashboard();
      }, "Создаём мероприятие…");
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error.message || "Не удалось создать мероприятие.";
        errorBox.classList.remove("hidden");
      } else {
        alert(error.message || "Не удалось создать мероприятие.");
      }
    } finally {
      createBtn.disabled = false;
    }
  });
}


async function updateManagerEventStatus(eventId, status) {
  const event = state.managerDraftEventsById?.[String(eventId)] || await api(`/events/${eventId}`);
  await api(`/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify({
      client_name: event.client_name,
      title: event.title,
      event_date: event.event_date,
      department_id: event.department_id,
      manager_id: event.manager_id,
      status,
      client_calc_type: event.client_calc_type,
      manager_percent: event.manager_percent,
      agency_commission_amount: event.agency_commission_amount,
      agency_commission_spread_enabled: event.agency_commission_spread_enabled,
      simplified_bank_tax_percent: event.simplified_bank_tax_percent,
    }),
  });
}


function renderManagerProfileModal(user) {
  const departments = state.bootstrap?.departments || [];
  return `
    <div class="profile-modal-content">
      <div class="form-grid">
        <label>Имя
          <input id="profileNameInput" value="${user.name || ""}" />
        </label>
        <label>Телефон
          <input id="profilePhoneInput" value="${formatPhoneKzPretty(user.phone)}" placeholder="+7 (___) ___ __ __" inputmode="tel" />
        </label>
        <label>Email
          <input id="profileEmailInput" value="${user.email || ""}" placeholder="name@example.com" />
        </label>
        <label>Отдел
          <select id="profileDepartmentInput">
            ${departments.map((department, index) => `
              <option value="${department.id}" ${Number(user.department_id) === Number(department.id) || (!user.department_id && index === 0) ? "selected" : ""}>${department.name}</option>
            `).join("")}
          </select>
        </label>
      </div>

      <div class="modal-actions">
        <button class="secondary" id="profileSaveBtn" type="button">Сохранить</button>
        <button class="ghost" id="profileCancelBtn" type="button">Отмена</button>
      </div>
      <div id="profileMessage" class="muted"></div>
    </div>
  `;
}

function openManagerProfileModal() {
  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

  const user = state.bootstrap?.user || {};
  backdrop.classList.remove("pin-modal-mode");
  backdrop.classList.add("profile-modal-mode");
  backdrop.classList.remove("hidden");
  title.textContent = "Данные менеджера";
  content.innerHTML = renderManagerProfileModal(user);

  const phoneInput = $("profilePhoneInput");
  if (phoneInput) {
    phoneInput.addEventListener("input", () => formatPhoneInputLive(phoneInput));
    phoneInput.addEventListener("blur", () => formatPhoneInputLive(phoneInput));
  }

  const close = () => {
    backdrop.classList.add("hidden");
    backdrop.classList.remove("profile-modal-mode");
  };
  $("profileCancelBtn")?.addEventListener("click", close);

  $("profileSaveBtn")?.addEventListener("click", async () => {
    const message = $("profileMessage");
    const saveBtn = $("profileSaveBtn");
    if (message) message.textContent = "";

    try {
      setButtonLoading(saveBtn, true, "Сохраняем…");
      const updatedUser = await api("/auth/me/profile", {
        method: "PATCH",
        body: JSON.stringify({
          name: $("profileNameInput").value,
          phone: $("profilePhoneInput").value,
          email: $("profileEmailInput").value,
          department_id: Number($("profileDepartmentInput").value),
        }),
      });

      const mergedUser = {
        ...(state.bootstrap.user || {}),
        ...updatedUser,
        email: updatedUser.email || $("profileEmailInput").value.trim(),
        phone: updatedUser.phone || $("profilePhoneInput").value.trim(),
        name: updatedUser.name || $("profileNameInput").value.trim(),
        department_id: updatedUser.department_id || Number($("profileDepartmentInput").value),
      };
      state.bootstrap.user = mergedUser;
      updateHeaderUserInfo(mergedUser);

      if (message) message.textContent = "Данные сохранены";
      close();
      await loadDashboard();
    } catch (error) {
      if (message) message.textContent = error.message || "Не удалось сохранить данные";
    } finally {
      setButtonLoading(saveBtn, false);
    }
  });
}


function attachManagerDashboardActions() {
  const createButtons = [
    document.getElementById("managerCreateEventShortcut"),
    document.querySelector(".manager-top-actions button"),
  ].filter(Boolean);

  createButtons.forEach((button) => {
    button.addEventListener("click", openManagerCreateModal);
  });

  document.querySelectorAll("[data-manager-event-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-manager-event-id");
      state.selectedManagerEventId = Number(eventId);

      document.querySelectorAll("[data-manager-event-id]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");

      await withLoading(async () => renderManagerEventDetail(eventId), "Открываем мероприятие…");
    });
  });


  document.querySelectorAll("[data-manager-event-save-draft]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-manager-event-save-draft");
      await withLoading(async () => {
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "draft");
        showDraftSavedHint();
        await loadDashboard();
      }, "Сохраняем черновик…");
    });
  });

  document.querySelectorAll("[data-manager-event-send-review]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-manager-event-send-review");
      if (!confirm("Отправить мероприятие Саше на проверку?")) return;

      await withLoading(async () => {
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "review");
        showDraftSavedHint();
        await loadDashboard();
      }, "Отправляем на проверку…");
    });
  });

}

function eventMonthKey(event) {
  return String(event?.event_date || "").slice(0, 7);
}

function emptyManagerDashboard(month) {
  const user = state.bootstrap?.user || {};
  return {
    month,
    manager_id: user.id || null,
    manager_name: user.name || "",
    department_id: user.department_id || null,
    department_name: user.department_name || null,
    include_drafts: true,
    personal_plan_amount: 0,
    fact_income_amount: 0,
    completion_percent: 0,
    remaining_to_plan: 0,
    events_count: 0,
    drafts_count: 0,
    payment_requests_count: 0,
    active_payment_requests_count: 0,
    events: [],
  };
}

function normalizeManagerDashboardForMonth(data, month) {
  const normalized = { ...(data || emptyManagerDashboard(month)) };
  normalized.month = month;

  const events = Array.isArray(normalized.events) ? normalized.events : [];
  normalized.events = events.filter((event) => eventMonthKey(event) === month);

  normalized.events_count = normalized.events.length;
  normalized.drafts_count = normalized.events.filter((event) => event.status === "draft").length;

  return normalized;
}

function clearManagerSelectedEventUi() {
  state.selectedManagerEventId = null;
  state.currentManagerEvent = null;
  state.currentManagerItems = [];
  state.currentManagerSummary = null;

  const holder = $("managerEventDetail");
  if (holder) {
    holder.innerHTML = `
      <div class="manager-empty-detail">
        <div class="empty-icon">▦</div>
        <h3>Загружаем выбранный период…</h3>
        <p class="muted">Список мероприятий обновляется.</p>
      </div>
    `;
  }
}


function renderManagerDashboard(data, paymentRequests = []) {
  const normalizedData = normalizeManagerDashboardForMonth(data, state.month);

  state.managerData = normalizedData;
  state.managerPaymentRequests = paymentRequests || [];

  $("adminTabs").classList.add("hidden");
  renderSummary([]);

  $("dashboardTitle").textContent = "Мои мероприятия";
  $("dashboardHint").textContent = "";

  $("dashboardContent").innerHTML = renderManagerDashboardLayout(normalizedData);

  attachPaymentRequestActions();
  attachManagerDashboardActions();
  scheduleMiniBadgeFit();

  const selected = getSelectedManagerEvent(normalizedData);
  const holder = $("managerEventDetail");

  if (selected) {
    state.selectedManagerEventId = selected.id;
    renderManagerEventDetail(selected.id);
  } else {
    state.selectedManagerEventId = null;
    state.currentManagerEvent = null;
    state.currentManagerItems = [];
    state.currentManagerSummary = null;

    if (holder) {
      holder.innerHTML = `
        <div class="manager-empty-detail">
          <div class="empty-icon">▦</div>
          <h3>Мероприятий за выбранный период нет</h3>
          <p class="muted">Выбери другой месяц или создай новое мероприятие.</p>
        </div>
      `;
    }
  }
}
function attachPlansModal() {
  const btn = document.getElementById("openPlansModalBtn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const managers = getManagers();
    $("plansModalBackdrop").classList.remove("hidden");
    $("plansModalContent").innerHTML = `
      <div class="form-grid">
        <label>Общий план компании
          <input value="${state.adminData?.company_plan_amount || ""}" />
        </label>
        <label>Доля Санжар, %
          <input value="66.67" />
        </label>
        <label>Доля Рауфаль, %
          <input value="33.33" />
        </label>
      </div>

      <div class="divider"></div>

      <h3>Индивидуальные планы менеджеров</h3>
      <p class="small-note">По умолчанию каждому менеджеру 1/8 общего плана. Сохранение подключим к backend следующим шагом.</p>

      <div class="table-wrap">
        <table>
          <thead><tr><th>Менеджер</th><th>Отдел</th><th>Процент от общего плана</th></tr></thead>
          <tbody>
            ${managers.map((manager) => `
              <tr>
                <td>${manager.name}</td>
                <td>${departmentNameById(manager.department_id)}</td>
                <td><input value="12.5" /></td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>

      <div class="divider"></div>
      <button class="secondary" disabled>Сохранение подключим следующим шагом</button>
    `;
  });
}

async function loadUsersForAdmin() {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return;

  try {
    state.users = await api("/users?include_inactive=false");
  } catch (error) {
    console.warn("Не удалось загрузить пользователей", error);
    state.users = [];
  }
}

async function loadDashboard() {
  const user = state.bootstrap.user;
  const month = selectedMonthValue();
  state.month = month;

  if (user.role === "admin") {
    try {
      await loadUsersForAdmin();
      renderAdminDashboard(await api(`/admin-dashboard?month=${month}&include_drafts=true&_=${Date.now()}`));
    } catch (error) {
      console.warn("Не удалось загрузить admin-dashboard за период", month, error);
      renderAdminEmptyDashboard(month, error);
    }
    return;
  }

  if (user.role === "department_head") {
    const [dashboard, requests] = await Promise.all([
      api(`/department-head-dashboard?department_id=${user.department_id}&month=${month}&include_drafts=true`),
      api("/payment-requests"),
    ]);
    renderDepartmentDashboard(dashboard, requests);
    return;
  }

  try {
    const [dashboard, requests] = await Promise.all([
      api(`/manager-dashboard?month=${month}&include_drafts=true&_=${Date.now()}`),
      api(`/payment-requests?_=${Date.now()}`),
    ]);
    renderManagerDashboard(dashboard, requests);
  } catch (error) {
    console.warn("Не удалось загрузить manager-dashboard за период", month, error);
    renderManagerDashboard(emptyManagerDashboard(month), []);
  }
}

async function boot() {
  if (!state.token) {
    showLogin();
    return;
  }

  try {
    state.bootstrap = await api("/app/bootstrap");
    showDashboardShell();

    const user = state.bootstrap.user;
    updateHeaderUserInfo(user);

    const pinBtn = document.getElementById("changePinOpenBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    if (pinBtn && logoutBtn && pinBtn.parentElement !== logoutBtn.parentElement) {
      pinBtn.classList.remove("ghost");
      pinBtn.classList.add("ghost");
      logoutBtn.parentElement.insertBefore(pinBtn, logoutBtn);
    }
    setupMonthYearSelectors();
    attachMonthYearSelectors();

    await loadDashboard();
  } catch (error) {
    console.warn(error);
    localStorage.removeItem("cf_token");
    state.token = "";
    showLogin();
  }
}

async function login() {
  const loginButton = $("loginBtn");
  const errorEl = $("loginError");
  if (errorEl) errorEl.classList.add("hidden");

  setButtonLoading(loginButton, true, "Входим…");

  try {
    let lastError = null;
    const attempts = getLoginAttempts();

    for (const payload of attempts) {
      try {
        const data = await api("/auth/login", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        state.token = data.access_token;
        localStorage.setItem("cf_token", state.token);
        await boot();
        return;
      } catch (error) {
        lastError = error;
      }
    }

    throw lastError || new Error("Не удалось войти");
  } catch (error) {
    if (errorEl) {
      errorEl.textContent = error.message;
      errorEl.classList.remove("hidden");
    }
    resetLoginButton();
  }
}


function openChangePinModal() {
  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

  backdrop.classList.remove("profile-modal-mode");
  backdrop.classList.add("pin-modal-mode");
  backdrop.classList.remove("hidden");
  title.textContent = "Смена PIN";
  content.innerHTML = `
    <div class="pin-modal-content">
      <p class="muted">Новый PIN минимум из 4 цифр.</p>

      <div class="pin-form-vertical">
        <label>Старый PIN
          <input id="pinOldInput" type="password" inputmode="numeric" autocomplete="current-password" />
        </label>
        <label>Новый PIN
          <input id="pinNewInput" type="password" inputmode="numeric" autocomplete="new-password" />
        </label>
      </div>

      <div class="modal-actions pin-actions">
        <button class="secondary" id="pinSaveBtn" type="button">Сменить PIN</button>
        <button class="ghost" id="pinCancelBtn" type="button">Отмена</button>
      </div>
      <div id="pinMessage" class="muted"></div>
    </div>
  `;

  $("pinCancelBtn")?.addEventListener("click", () => { backdrop.classList.add("hidden"); backdrop.classList.remove("pin-modal-mode"); });
  $("pinSaveBtn")?.addEventListener("click", changePin);

  ["pinOldInput", "pinNewInput"].forEach((id) => {
    const input = $(id);
    if (!input) return;
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") changePin();
    });
  });

  $("pinOldInput")?.focus();
}


async function changePin() {
  const msg = $("pinMessage") || $("changePinMessage");
  const button = $("pinSaveBtn") || $("changePinBtn");
  const oldInput = $("pinOldInput") || $("oldPin");
  const newInput = $("pinNewInput") || $("newPin");
  if (msg) msg.textContent = "";

  try {
    setButtonLoading(button, true, "Сохраняем…");
    const data = await api("/auth/change-pin", {
      method: "PATCH",
      body: JSON.stringify({
        old_pin: oldInput?.value || "",
        new_pin: newInput?.value || "",
      }),
    });

    if (msg) msg.textContent = data.message || "PIN изменён";
    if (oldInput) oldInput.value = "";
    if (newInput) newInput.value = "";

    setTimeout(() => {
      $("eventModalBackdrop")?.classList.add("hidden");
      $("eventModalBackdrop")?.classList.remove("pin-modal-mode");
      $("eventModalBackdrop")?.classList.remove("profile-modal-mode");
    }, 450);
  } catch (error) {
    if (msg) msg.textContent = error.message;
  } finally {
    setButtonLoading(button, false);
  }
}

function attachLoginHandlers() {
  const loginButton = $("loginBtn");
  if (loginButton) loginButton.onclick = login;

  attachAuthTabs();

  ["loginName", "loginPin"].forEach((id) => {
    const input = $(id);
    if (!input || input.dataset.enterAttached === "1") return;
    input.dataset.enterAttached = "1";
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        login();
      }
    });
  });
}

attachLoginHandlers();

$("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("cf_token");
  state.token = "";
  state.bootstrap = null;
  const pinInput = $("loginPin");
  if (pinInput) pinInput.value = "";
  showLogin();
});

$("reloadBtn").addEventListener("click", () => {
  withLoading(loadDashboard, "Обновляем данные…").catch((error) => alert(error.message));
});

$("changePinOpenBtn").addEventListener("click", openChangePinModal);

const legacyChangePinBtn = $("changePinBtn");
if (legacyChangePinBtn) legacyChangePinBtn.addEventListener("click", changePin);

$("eventModalCloseBtn").addEventListener("click", () => {
  $("eventModalBackdrop").classList.add("hidden");
  $("eventModalBackdrop").classList.remove("pin-modal-mode");
  $("eventModalBackdrop").classList.remove("profile-modal-mode");
  $("eventModalBackdrop").classList.remove("payment-modal-mode");
});

$("plansModalCloseBtn").addEventListener("click", () => {
  $("plansModalBackdrop").classList.add("hidden");
});

document.addEventListener("click", (event) => {
  if (event.target.closest("[data-manager-action-dropdown]")) return;
  if (event.target.closest("[data-manager-event-transfer], [data-manager-event-coauthor]")) return;
  closeManagerActionDropdown();
});

window.addEventListener("resize", () => scheduleMiniBadgeFit());

boot();
