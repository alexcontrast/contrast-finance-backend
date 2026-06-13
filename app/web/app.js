
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


    /* v0.35.91: компактные имена менеджеров в обзоре */
    .manager-progress-main .manager-progress-name {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      max-width: 100%;
      min-width: 0;
      font-size: 13px;
      line-height: 1.05;
      white-space: nowrap;
    }

    .manager-progress-main .manager-progress-name span {
      display: block;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .manager-events-count-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      border-radius: 999px;
      background: rgba(38, 98, 35, .11);
      border: 1px solid rgba(38, 98, 35, .18);
      color: #27631f;
      font-size: 11px;
      font-style: normal;
      font-weight: 950;
      line-height: 1;
      flex: 0 0 auto;
    }


    .manager-champion-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      border-radius: 999px;
      background: rgba(105, 255, 0, .18);
      border: 1px solid rgba(105, 255, 0, .32);
      font-size: 12px;
      font-style: normal;
      line-height: 1;
      flex: 0 0 auto;
    }


    /* v0.35.92: мероприятия окрашиваются по отделу, не по статусу */
    .admin-events-table tbody tr.admin-event-row td,
    .admin-events-table tbody tr.admin-event-row td strong {
      color: #171a16 !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-sanzhar td {
      background: rgba(225, 246, 218, .86) !important;
      border-color: rgba(53, 150, 57, .14) !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-raufal td {
      background: rgba(226, 241, 255, .86) !important;
      border-color: rgba(46, 126, 190, .13) !important;
    }

    .admin-events-table tbody tr.admin-event-row:not(.department-sanzhar):not(.department-raufal) td {
      background: rgba(244, 247, 241, .88) !important;
      border-color: rgba(120, 140, 110, .13) !important;
    }

    .admin-events-table tbody tr.admin-event-row.status-tone-draft td,
    .admin-events-table tbody tr.admin-event-row.status-tone-review td,
    .admin-events-table tbody tr.admin-event-row.status-tone-accepted td {
      color: #171a16 !important;
    }

    .admin-events-table .admin-event-status-badge {
      color: #171a16 !important;
    }


    /* v0.35.93: полноценная заливка бейджа статуса мероприятия */
    .admin-events-table .admin-event-status-badge {
      box-shadow: none !important;
      border-width: 1px !important;
      font-weight: 950 !important;
    }

    .admin-events-table .admin-event-status-badge.draft,
    .admin-events-table .admin-event-status-badge.revision {
      background: rgba(244, 247, 241, .98) !important;
      border-color: rgba(125, 133, 118, .28) !important;
      color: #52594f !important;
    }

    .admin-events-table .admin-event-status-badge.review {
      background: rgba(255, 239, 196, .98) !important;
      border-color: rgba(199, 151, 40, .34) !important;
      color: #8a6207 !important;
    }

    .admin-events-table .admin-event-status-badge.completed,
    .admin-events-table .admin-event-status-badge.archive,
    .admin-events-table .admin-event-status-badge.archived {
      background: rgba(216, 244, 210, .98) !important;
      border-color: rgba(53, 150, 57, .28) !important;
      color: #1f7a35 !important;
    }

    .admin-events-table .admin-event-status-badge.cancelled {
      background: rgba(255, 228, 222, .98) !important;
      border-color: rgba(205, 86, 67, .28) !important;
      color: #b84835 !important;
    }

    /* v0.35.93: градиент отделов для соавторства из разных отделов */
    .admin-events-table tbody tr.admin-event-row.department-mixed-sanzhar-raufal td {
      background: linear-gradient(90deg, rgba(225, 246, 218, .90) 0%, rgba(225, 246, 218, .74) 45%, rgba(226, 241, 255, .74) 55%, rgba(226, 241, 255, .90) 100%) !important;
      border-color: rgba(68, 145, 120, .14) !important;
      color: #171a16 !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-mixed td {
      background: linear-gradient(90deg, rgba(225, 246, 218, .82), rgba(244, 247, 241, .86), rgba(226, 241, 255, .82)) !important;
      border-color: rgba(120, 140, 110, .13) !important;
      color: #171a16 !important;
    }


    /* v0.35.94: правильные цвета отделов в строках мероприятий */
    .admin-events-table tbody tr.admin-event-row.department-sanzhar td {
      background: rgba(226, 241, 255, .92) !important;
      border-color: rgba(46, 126, 190, .16) !important;
      color: #171a16 !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-raufal td {
      background: rgba(255, 232, 210, .92) !important;
      border-color: rgba(218, 139, 78, .18) !important;
      color: #171a16 !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-mixed-sanzhar-raufal td {
      background: linear-gradient(90deg,
        rgba(226, 241, 255, .94) 0%,
        rgba(226, 241, 255, .94) 50%,
        rgba(255, 232, 210, .94) 50%,
        rgba(255, 232, 210, .94) 100%
      ) !important;
      border-color: rgba(150, 136, 118, .18) !important;
      color: #171a16 !important;
    }

    .admin-events-table tbody tr.admin-event-row.department-mixed td {
      background: linear-gradient(90deg,
        rgba(226, 241, 255, .94) 0%,
        rgba(226, 241, 255, .94) 50%,
        rgba(255, 232, 210, .94) 50%,
        rgba(255, 232, 210, .94) 100%
      ) !important;
      border-color: rgba(150, 136, 118, .18) !important;
      color: #171a16 !important;
    }


    /* v0.35.95: ЗП менеджера отдельной карточкой в админской модалке */
    .manager-salary-metric {
      background: rgba(244, 247, 241, .96) !important;
      border-color: rgba(126, 143, 116, .22) !important;
    }

    .manager-salary-metric .salary-request-btn {
      margin-top: 10px;
      min-height: 32px;
      padding: 6px 12px;
      border-radius: 12px;
      font-size: 12px;
    }


    /* v0.35.96: строки надбавок заказчику в смете админской модалки */
    .estimate-table tr.estimate-top-charge-row td {
      background: rgba(242, 250, 236, .92) !important;
      border-top: 1px solid rgba(80, 210, 40, .22);
      color: #171a16;
    }

    .estimate-table tr.estimate-top-charge-row td:first-child {
      border-left: 4px solid rgba(80, 210, 40, .86);
    }

    .estimate-top-charge-row td strong {
      display: block;
      color: #171a16;
    }

    .estimate-top-charge-row td span {
      display: block;
      margin-top: 2px;
      color: rgba(80, 90, 74, .78);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
    }


    /* v0.35.97: надбавки заказчику в смете без лишнего выделения */
    .estimate-table tr.estimate-top-charge-row td {
      background: rgba(242, 250, 236, .92) !important;
      border-top: 1px solid rgba(80, 210, 40, .18) !important;
      color: #171a16 !important;
    }

    .estimate-table tr.estimate-top-charge-row td:first-child {
      border-left: none !important;
    }

    .estimate-top-charge-row td strong {
      display: inline !important;
      color: #171a16 !important;
    }


    /* v0.36.00: таблица мероприятий в одну строку */
    .admin-events-table {
      table-layout: auto !important;
      width: max-content !important;
      min-width: 100% !important;
    }

    .admin-events-table th,
    .admin-events-table td {
      white-space: nowrap !important;
      vertical-align: middle !important;
    }

    .admin-events-table td:nth-child(4),
    .admin-events-table td:nth-child(5) {
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .admin-events-table th {
      font-size: 12px !important;
      letter-spacing: .07em !important;
    }

    .admin-events-table .admin-event-status-badge {
      white-space: nowrap !important;
      display: inline-flex !important;
      min-width: max-content !important;
    }

    .admin-events-table-wrap {
      overflow-x: auto !important;
    }


    /* v0.40.24: цвета столбцов сметы привязаны к смысловым классам, не к nth-child */
    .estimate-table th.vat-col,
    .estimate-table td.vat-col {
      background: rgba(220, 244, 252, .72) !important;
    }

    .estimate-table th.deduction-col,
    .estimate-table td.deduction-col {
      background: rgba(237, 226, 248, .72) !important;
    }

    .estimate-table th.commission-col,
    .estimate-table td.commission-col,
    .estimate-table th.method-col,
    .estimate-table td.method-col {
      background: #f4f7ec !important;
    }

    /* v0.36.01: компактная таблица мероприятий без горизонтального скролла */
    .admin-events-table {
      table-layout: fixed !important;
      width: 100% !important;
      min-width: 0 !important;
      font-size: 12px !important;
    }

    .admin-events-table th,
    .admin-events-table td {
      padding: 8px 9px !important;
      font-size: 12px !important;
      line-height: 1.12 !important;
      white-space: nowrap !important;
    }

    .admin-events-table th {
      font-size: 10.5px !important;
      letter-spacing: .055em !important;
    }

    .admin-events-table td:nth-child(1) { width: 82px; }
    .admin-events-table td:nth-child(2) { width: 136px; }
    .admin-events-table td:nth-child(3) { width: 120px; }
    .admin-events-table td:nth-child(4) { width: 150px; }
    .admin-events-table td:nth-child(5) { width: 96px; }
    .admin-events-table td:nth-child(6) { width: 104px; }
    .admin-events-table td:nth-child(7),
    .admin-events-table td:nth-child(8),
    .admin-events-table td:nth-child(9) { width: 92px; }
    .admin-events-table td:nth-child(10) { width: 54px; }

    .admin-events-table td:nth-child(2),
    .admin-events-table td:nth-child(3),
    .admin-events-table td:nth-child(4),
    .admin-events-table td:nth-child(5) {
      overflow: hidden !important;
      text-overflow: ellipsis !important;
    }

    .admin-events-table .admin-event-status-badge {
      font-size: 10.5px !important;
      padding: 4px 8px !important;
      white-space: nowrap !important;
      min-width: 0 !important;
    }

    .admin-events-table-wrap {
      overflow-x: visible !important;
    }


    /* v0.36.02: точная раскладка ширин таблицы мероприятий */
    .admin-events-table {
      table-layout: fixed !important;
      width: 100% !important;
      min-width: 0 !important;
      font-size: 11.5px !important;
    }

    .admin-events-table th,
    .admin-events-table td {
      padding: 7px 7px !important;
      font-size: 11.5px !important;
      line-height: 1.08 !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
    }

    .admin-events-table th {
      font-size: 9.8px !important;
      letter-spacing: .045em !important;
    }

    .admin-events-table th:nth-child(1),
    .admin-events-table td:nth-child(1) {
      width: 76px !important;
      min-width: 76px !important;
      max-width: 76px !important;
    }

    .admin-events-table th:nth-child(2),
    .admin-events-table td:nth-child(2) {
      width: 16% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(3),
    .admin-events-table td:nth-child(3) {
      width: 14% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(4),
    .admin-events-table td:nth-child(4) {
      width: 17% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(5),
    .admin-events-table td:nth-child(5) {
      width: 94px !important;
      min-width: 94px !important;
      max-width: 94px !important;
    }

    .admin-events-table th:nth-child(6),
    .admin-events-table td:nth-child(6) {
      width: 92px !important;
      min-width: 92px !important;
      max-width: 92px !important;
    }

    .admin-events-table th:nth-child(7),
    .admin-events-table td:nth-child(7),
    .admin-events-table th:nth-child(8),
    .admin-events-table td:nth-child(8),
    .admin-events-table th:nth-child(9),
    .admin-events-table td:nth-child(9) {
      width: 84px !important;
      min-width: 84px !important;
      max-width: 84px !important;
    }

    .admin-events-table th:nth-child(10),
    .admin-events-table td:nth-child(10) {
      width: 42px !important;
      min-width: 42px !important;
      max-width: 42px !important;
      text-align: center !important;
    }

    .admin-events-table td:nth-child(7),
    .admin-events-table td:nth-child(8),
    .admin-events-table td:nth-child(9) {
      font-variant-numeric: tabular-nums;
    }

    .admin-events-table .admin-event-status-badge {
      font-size: 9.8px !important;
      padding: 4px 6px !important;
      max-width: 100% !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      white-space: nowrap !important;
    }

    .admin-events-table-wrap {
      overflow-x: visible !important;
    }


    /* v0.36.03: слово "Заявки" в шапке мероприятий помещается полностью */
    .admin-events-table th:nth-child(10),
    .admin-events-table td:nth-child(10) {
      width: 56px !important;
      min-width: 56px !important;
      max-width: 56px !important;
      text-align: center !important;
    }

    .admin-events-table th:nth-child(10) {
      font-size: 9.4px !important;
      letter-spacing: .035em !important;
      overflow: visible !important;
      text-overflow: clip !important;
    }

    .admin-events-table th:nth-child(7),
    .admin-events-table td:nth-child(7),
    .admin-events-table th:nth-child(8),
    .admin-events-table td:nth-child(8),
    .admin-events-table th:nth-child(9),
    .admin-events-table td:nth-child(9) {
      width: 80px !important;
      min-width: 80px !important;
      max-width: 80px !important;
    }


    /* v0.36.04: действия админа в модалке мероприятия */
    #eventModalActions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex-wrap: wrap;
      margin-left: auto;
      margin-right: 8px;
    }

    #eventModalActions button {
      min-height: 38px;
      padding: 8px 13px;
      border-radius: 14px;
      font-size: 13px;
      font-weight: 900;
    }

    #eventModalActions .danger-btn {
      color: #b84835 !important;
      background: rgba(255, 235, 230, .96) !important;
      border-color: rgba(205, 86, 67, .38) !important;
    }


    /* v0.36.05: выравнивание кнопок действий мероприятия */
    #eventModalActions {
      align-items: center !important;
      gap: 8px !important;
    }

    #eventModalActions .event-action-btn {
      min-height: 42px !important;
      height: 42px !important;
      padding: 0 18px !important;
      border-radius: 16px !important;
      font-size: 14px !important;
      font-weight: 950 !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      line-height: 1 !important;
      white-space: nowrap !important;
    }

    #eventModalActions .event-accept-btn {
      background: rgba(216, 244, 210, .98) !important;
      border: 1px solid rgba(53, 150, 57, .35) !important;
      color: #1f7a35 !important;
    }

    #eventModalActions .event-cash-btn {
      background: #7CFF35 !important;
      border: 1px solid rgba(72, 195, 12, .62) !important;
      color: #173f0b !important;
      box-shadow: 0 10px 24px rgba(124, 255, 53, .22) !important;
    }

    #eventModalActions .event-revision-btn {
      background: rgba(244, 247, 241, .98) !important;
      border: 1px solid rgba(125, 133, 118, .32) !important;
      color: #52594f !important;
    }

    #eventModalActions .event-delete-btn {
      min-height: 42px !important;
      height: 42px !important;
    }


    /* v0.36.06: статусы Принято / Деньги в кассе и неактивные админ-кнопки */
    .status.accepted,
    .admin-events-table .admin-event-status-badge.accepted {
      background: rgba(216, 244, 210, .98) !important;
      border-color: rgba(53, 150, 57, .35) !important;
      color: #1f7a35 !important;
      box-shadow: none !important;
    }

    .status.cash_received,
    .admin-events-table .admin-event-status-badge.cash_received {
      background: #7CFF35 !important;
      border-color: rgba(72, 195, 12, .62) !important;
      color: #173f0b !important;
      box-shadow: 0 8px 18px rgba(124, 255, 53, .18) !important;
    }

    #eventModalActions .event-action-btn.is-disabled,
    #eventModalActions .event-action-btn:disabled {
      opacity: .48 !important;
      filter: grayscale(.25) !important;
      cursor: not-allowed !important;
      box-shadow: none !important;
      pointer-events: none !important;
    }


    /* v0.36.07: кнопка "Вернуть в работу" */
    #eventModalActions .event-return-btn {
      background: rgba(244, 247, 241, .98) !important;
      border: 1px solid rgba(125, 133, 118, .32) !important;
      color: #52594f !important;
    }


    /* v0.36.08: статус денег в кассе виден в модалке, повторная кнопка отключена */
    .event-request-status-badge.cash_received,
    .event-request-cash-note .status.cash_received {
      background: #7CFF35 !important;
      border-color: rgba(72, 195, 12, .62) !important;
      color: #173f0b !important;
      box-shadow: 0 8px 18px rgba(124, 255, 53, .16) !important;
      white-space: nowrap !important;
    }

    .event-request-cash-note {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 10px 0 12px;
      padding: 10px 12px;
      border-radius: 16px;
      background: rgba(124, 255, 53, .10);
      border: 1px solid rgba(72, 195, 12, .20);
      color: #264620;
      font-size: 13px;
      font-weight: 800;
    }


    /* v0.36.09: миникарточка мероприятия "Деньги в кассе" зелёная как "Принято" */
    .manager-event-card.status-cash_received,
    .manager-event-card.cash_received,
    .event-card.status-cash_received,
    .event-card.cash_received {
      background: rgba(216, 244, 210, .98) !important;
      border-color: rgba(53, 150, 57, .35) !important;
      color: #1f3f24 !important;
    }

    .manager-event-card.status-cash_received .status,
    .manager-event-card.cash_received .status,
    .event-card.status-cash_received .status,
    .event-card.cash_received .status {
      background: rgba(216, 244, 210, .98) !important;
      border-color: rgba(53, 150, 57, .35) !important;
      color: #1f7a35 !important;
    }


    /* v0.37.00: money_status отдельно от status */
    .admin-event-money-badge {
      margin-left: 6px !important;
      display: inline-flex !important;
      vertical-align: middle !important;
      white-space: nowrap !important;
      background: #7CFF35 !important;
      border-color: rgba(72, 195, 12, .62) !important;
      color: #173f0b !important;
    }

    .status.waiting_money {
      background: rgba(245, 245, 245, .92) !important;
      border-color: rgba(150, 150, 150, .28) !important;
      color: #686868 !important;
    }


    /* v0.37.02: отдельная колонка "Статус денег" в мероприятиях */
    .admin-events-table th:nth-child(1),
    .admin-events-table td:nth-child(1) {
      width: 70px !important;
      min-width: 70px !important;
      max-width: 70px !important;
    }

    .admin-events-table th:nth-child(2),
    .admin-events-table td:nth-child(2) {
      width: 13% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(3),
    .admin-events-table td:nth-child(3) {
      width: 12% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(4),
    .admin-events-table td:nth-child(4) {
      width: 14% !important;
      min-width: 0 !important;
    }

    .admin-events-table th:nth-child(5),
    .admin-events-table td:nth-child(5) {
      width: 82px !important;
      min-width: 82px !important;
      max-width: 82px !important;
    }

    .admin-events-table th:nth-child(6),
    .admin-events-table td:nth-child(6) {
      width: 84px !important;
      min-width: 84px !important;
      max-width: 84px !important;
    }

    .admin-events-table th:nth-child(7),
    .admin-events-table td:nth-child(7) {
      width: 104px !important;
      min-width: 104px !important;
      max-width: 104px !important;
    }

    .admin-events-table th:nth-child(8),
    .admin-events-table td:nth-child(8),
    .admin-events-table th:nth-child(9),
    .admin-events-table td:nth-child(9),
    .admin-events-table th:nth-child(10),
    .admin-events-table td:nth-child(10) {
      width: 76px !important;
      min-width: 76px !important;
      max-width: 76px !important;
    }

    .admin-events-table th:nth-child(11),
    .admin-events-table td:nth-child(11) {
      width: 52px !important;
      min-width: 52px !important;
      max-width: 52px !important;
      text-align: center !important;
    }

    .admin-event-money-badge {
      margin-left: 0 !important;
      max-width: 100% !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      justify-content: center !important;
    }


    /* v0.37.03: размеры бейджей денег и ровные ряды кнопок */
    .admin-event-money-badge,
    .request-money-badge,
    .event-request-status-badge,
    .request-status-badge {
      min-height: 24px !important;
      height: 24px !important;
      padding: 4px 8px !important;
      border-radius: 999px !important;
      font-size: 10.5px !important;
      line-height: 1 !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      white-space: nowrap !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }

    .admin-event-money-badge {
      margin-left: 0 !important;
    }

    .request-actions-row,
    .inline-actions,
    .coauthor-actions,
    .share-actions,
    .coauthor-row-actions {
      display: flex !important;
      align-items: center !important;
      gap: 8px !important;
      flex-wrap: nowrap !important;
    }

    .request-actions-row button,
    .inline-actions button,
    .coauthor-actions button,
    .share-actions button,
    .coauthor-row-actions button {
      white-space: nowrap !important;
      flex: 0 0 auto !important;
    }

    #eventModalActions {
      flex-wrap: nowrap !important;
    }


    /* v0.40.24: compact admin event editor columns */
    #eventModalBackdrop.admin-event-edit-mode .estimate-tabs {
      display: none !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .modal,
    #eventModalBackdrop.admin-event-edit-mode .event-modal,
    #eventModalBackdrop.admin-event-edit-mode .modal-card {
      width: min(1500px, calc(100vw - 24px)) !important;
      max-width: 1500px !important;
    }

    #eventModalBackdrop.admin-event-edit-mode #eventModalContent,
    #eventModalBackdrop.admin-event-edit-mode .estimate-table-wrap {
      overflow-x: hidden !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table {
      width: 100% !important;
      min-width: 0 !important;
      table-layout: fixed !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table th,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table td {
      padding: 6px 5px !important;
      font-size: 11px !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      white-space: nowrap !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table input,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table select {
      min-height: 28px !important;
      padding: 4px 5px !important;
      font-size: 11px !important;
      border-radius: 7px !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table .drag-col,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table col.drag-col {
      width: 26px !important;
      min-width: 26px !important;
      max-width: 26px !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table .drag-handle {
      width: 16px !important;
      height: 16px !important;
      font-size: 10px !important;
      border-radius: 4px !important;
    }


    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table th.kgd-col,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table td.kgd-col {
      width: 42px !important;
      min-width: 42px !important;
      max-width: 42px !important;
      padding-left: 2px !important;
      padding-right: 2px !important;
      text-align: center !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table td.kgd-col .icon-btn {
      width: 28px !important;
      min-width: 28px !important;
      height: 28px !important;
      padding: 0 !important;
      border-radius: 8px !important;
    }


    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table th.kgd-col,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table td.kgd-col {
      background: #f4f7ec !important;
    }

    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table th.paid-col,
    #eventModalBackdrop.admin-event-edit-mode .internal-estimate-table td.paid-col {
      background: #fff !important;
    }


    /* v0.37.04: статус денег "Отменено" */
    .status.cancelled.request-money-badge,
    .request-money-badge.cancelled,
    .event-request-status-badge.cancelled {
      background: rgba(255, 232, 226, .95) !important;
      border-color: rgba(194, 82, 64, .34) !important;
      color: #a33b2f !important;
    }


    /* v0.37.05: вернуть нормальную ширину модалки мероприятия после money_status-таблиц */
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .event-modal,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-card {
      width: min(1280px, calc(100vw - 32px)) !important;
      max-width: 1280px !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalContent {
      max-width: 100% !important;
      overflow-x: hidden !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards {
      grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
      gap: 12px !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards .card.metric {
      min-width: 0 !important;
      padding: 14px 14px !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards .value {
      font-size: clamp(18px, 1.65vw, 26px) !important;
      line-height: 1.05 !important;
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards .label {
      white-space: normal !important;
      line-height: 1.15 !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table-wrap,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection .table-wrap {
      width: 100% !important;
      max-width: 100% !important;
      overflow-x: auto !important;
      overscroll-behavior-x: contain !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection table {
      width: 100% !important;
      min-width: 980px !important;
      table-layout: fixed !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection th,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection td {
      min-width: 0 !important;
      max-width: none !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      vertical-align: middle !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(1),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(1) {
      width: 28% !important;
      white-space: normal !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(2),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(2),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(3),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(3),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(4),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(4),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(5),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(5),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(6),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(6) {
      width: 11% !important;
      white-space: nowrap !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table th:nth-child(7),
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .estimate-table td:nth-child(7) {
      width: 16% !important;
      white-space: nowrap !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection th,
    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection td {
      font-size: 12px !important;
      padding: 8px 8px !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection .request-actions-row {
      justify-content: flex-start !important;
      gap: 6px !important;
    }

    #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) #eventModalRequestsSection .request-actions-row button {
      padding: 7px 9px !important;
      font-size: 11px !important;
    }

    @media (max-width: 900px) {
      #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
      }

      #eventModalBackdrop:not(.payment-modal-mode):not(.pin-modal-mode):not(.profile-modal-mode):not(.manager-payments-modal):not(.manager-requests-modal-mode) .modal-metric-cards .value {
        font-size: 20px !important;
      }
    }


    /* v0.37.09: запрет удаления мероприятия, если деньги в кассе */
    button.is-disabled,
    button:disabled,
    .event-delete-btn.is-disabled,
    .danger-btn.is-disabled {
      opacity: .48 !important;
      filter: grayscale(.25) !important;
      cursor: not-allowed !important;
      box-shadow: none !important;
    }

    button:disabled,
    button.is-disabled {
      pointer-events: none !important;
    }


    /* v0.37.10: жёсткая блокировка редактирования менеджером статуса "На проверке" */
    .manager-event-card.is-readonly input,
    .manager-event-card.is-readonly select,
    .manager-event-card.is-readonly textarea,
    .manager-event-card.is-readonly [data-item-field],
    .manager-event-card.is-readonly [data-event-field] {
      pointer-events: none !important;
      user-select: none !important;
    }

    .manager-event-card.is-readonly .save-draft-btn,
    .manager-event-card.is-readonly [data-manager-event-send-review],
    .manager-event-card.is-readonly .disabled-action {
      pointer-events: none !important;
      opacity: .48 !important;
      cursor: not-allowed !important;
      box-shadow: none !important;
    }


    /* v0.37.14: "Мои оплаты" реально по ширине внутренних карточек + cache-bust через index.html */
    #plansModalBackdrop.manager-payments-modal .modal,
    #plansModalBackdrop.manager-payments-modal .modal-card,
    #plansModalBackdrop.manager-payments-modal .event-modal,
    #eventModalBackdrop.manager-payments-modal .modal,
    #eventModalBackdrop.manager-payments-modal .modal-card,
    #eventModalBackdrop.manager-payments-modal .event-modal {
      width: fit-content !important;
      max-width: calc(100vw - 32px) !important;
      min-width: 0 !important;
      padding-left: 18px !important;
      padding-right: 18px !important;
    }

    #plansModalBackdrop.manager-payments-modal .modal-head,
    #eventModalBackdrop.manager-payments-modal .modal-head {
      display: flex !important;
      align-items: flex-start !important;
      justify-content: space-between !important;
      gap: 16px !important;
      flex-wrap: nowrap !important;
    }

    #plansModalBackdrop.manager-payments-modal .modal-head > div,
    #eventModalBackdrop.manager-payments-modal .modal-head > div {
      min-width: 0 !important;
      flex: 1 1 auto !important;
    }

    #plansModalBackdrop.manager-payments-modal .modal-head h2,
    #eventModalBackdrop.manager-payments-modal .modal-head h2 {
      margin: 0 !important;
      white-space: normal !important;
      overflow-wrap: anywhere !important;
    }

    #plansModalBackdrop.manager-payments-modal .modal-head button,
    #eventModalBackdrop.manager-payments-modal .modal-head button {
      flex: 0 0 auto !important;
      white-space: nowrap !important;
      align-self: flex-start !important;
    }

    #plansModalBackdrop.manager-payments-modal #plansModalContent,
    #eventModalBackdrop.manager-payments-modal #eventModalContent {
      width: fit-content !important;
      max-width: 100% !important;
      margin-left: auto !important;
      margin-right: auto !important;
      overflow-x: hidden !important;
    }

    #eventModalBackdrop.manager-payments-modal .manager-event-requests-modal,
    #eventModalBackdrop.manager-payments-modal .compact-payments-modal,
    #eventModalBackdrop.manager-payments-modal .grouped-payments-modal,
    #eventModalBackdrop.manager-payments-modal .compact-grouped-payments {
      width: fit-content !important;
      min-width: 0 !important;
      max-width: 100% !important;
      margin-left: auto !important;
      margin-right: auto !important;
    }

    #eventModalBackdrop.manager-payments-modal .manager-payment-position-group.compact {
      width: fit-content !important;
      min-width: 0 !important;
      max-width: 100% !important;
    }

    #plansModalBackdrop.manager-payments-modal .table-wrap,
    #plansModalBackdrop.manager-payments-modal .payments-list,
    #plansModalBackdrop.manager-payments-modal .manager-payments-list,
    #eventModalBackdrop.manager-payments-modal .table-wrap,
    #eventModalBackdrop.manager-payments-modal .payments-list,
    #eventModalBackdrop.manager-payments-modal .manager-payments-list {
      width: 100% !important;
      max-width: 100% !important;
      overflow-x: auto !important;
    }

    #plansModalBackdrop.manager-payments-modal table,
    #eventModalBackdrop.manager-payments-modal table {
      width: 100% !important;
      min-width: 720px !important;
      table-layout: fixed !important;
    }

    #plansModalBackdrop.manager-payments-modal th,
    #plansModalBackdrop.manager-payments-modal td,
    #eventModalBackdrop.manager-payments-modal th,
    #eventModalBackdrop.manager-payments-modal td {
      min-width: 0 !important;
      max-width: none !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      vertical-align: middle !important;
      font-size: 12px !important;
      padding: 8px 8px !important;
    }

    #plansModalBackdrop.manager-payments-modal .request-actions-row,
    #eventModalBackdrop.manager-payments-modal .request-actions-row {
      justify-content: flex-start !important;
      gap: 6px !important;
      flex-wrap: nowrap !important;
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
  eventCustomerFilter: "all",
  eventManagerFilter: "all",
  eventStatusFilter: "all",
  eventSearch: "",
  activeAdminTab: "overview",
  activeDepartmentHeadTab: "overview",
  activeManagerTab: "events",
  selectedManagerEventId: null,
  managerEstimateTab: "external",
  managerDraftItemsByEventId: {},
  managerDraftDeletedByEventId: {},
  managerDraftEventsById: {},
  managerDraftTempSeq: 1,
  adminEventEditModeId: null,
  adminData: null,
  departmentHeadData: null,
  users: [],
  monthlyPlans: [],
  monthlyPlansYear: null,
  closingPanelData: null,
  closingEditingExpenseId: null,
  closingCalcRefreshTimer: null,
  closingCalcRefreshSeq: 0,
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
      state.eventCustomerFilter = "all";
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
    accepted: "Принято",
    completed: "Завершено",
    cash_received: "Деньги в кассе",
    waiting_money: "Ждём денег",
    cancelled: "Отменено",
    new: "Новая",
    to_pay: "На оплату",
    paid: "Оплачено",
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
    ip_contrast_event: "Contrast Event",
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

  const alwaysFreshFields = [
    "status",
    "money_status",
    "is_coauthored",
    "coauthor_name",
    "coauthor_user_id",
    "owner_manager_id",
    "owner_manager_name",
    "share_percent",
    "active_payment_requests_count",
    "payment_requests_count",
  ];

  if (!state.managerDraftEventsById[key]) {
    state.managerDraftEventsById[key] = JSON.parse(JSON.stringify(event));
  } else {
    // Локальный черновик хранит редактируемые поля, но рабочий статус
    // всегда должен приходить свежим с сервера. Иначе после отправки
    // "На проверку" карточка могла оставаться редактируемой как draft/revision.
    alwaysFreshFields.forEach((field) => {
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


function requestMoneyStatus(request) {
  if (["rejected", "cancelled"].includes(request?.status)) return "cancelled";
  return request?.money_status || (request?.status === "cash_received" ? "cash_received" : "waiting_money");
}

function eventMoneyStatus(event) {
  return event?.money_status || (event?.status === "cash_received" ? "cash_received" : "waiting_money");
}

function eventIsMoneyArchive(event) {
  return event?.status === "accepted" && eventMoneyStatus(event) === "cash_received";
}

function modalFilteredRequests(requests, status) {
  if (!status || status === "all") return requests || [];
  if (status === "active") {
    return (requests || []).filter((request) => !["rejected", "cancelled"].includes(request.status));
  }
  if (status === "archive") {
    return (requests || []).filter((request) => ["rejected", "cancelled"].includes(request.status));
  }
  if (status === "cash_received") {
    return (requests || []).filter((request) => requestMoneyStatus(request) === "cash_received");
  }
  if (status === "waiting_money") {
    return (requests || []).filter((request) => requestMoneyStatus(request) !== "cash_received");
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
    ${(requests || []).some((request) => requestMoneyStatus(request) === "cash_received") ? `
      <div class="event-request-cash-note">
        <span class="status cash_received event-request-status-badge">Деньги в кассе</span>
        <span>По мероприятию уже есть оплаты со статусом “Деньги в кассе”.</span>
      </div>
    ` : ""}

    <div class="filters-row">
      <label class="compact-label">Статус оплаты
        <select id="eventModalRequestStatusFilter">
          <option value="all" ${selectedStatus === "all" ? "selected" : ""}>Все</option>
          <option value="active" ${selectedStatus === "active" ? "selected" : ""}>Активные</option>
          <option value="new" ${selectedStatus === "new" ? "selected" : ""}>Новая</option>
          <option value="paid" ${selectedStatus === "paid" ? "selected" : ""}>Оплачено</option>
          <option value="cash_received" ${selectedStatus === "cash_received" ? "selected" : ""}>Деньги в кассе</option>
          <option value="waiting_money" ${selectedStatus === "waiting_money" ? "selected" : ""}>Ждём денег</option>
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
              <th>Статус оплаты</th>
              <th>Статус денег</th>
              <th>Кнопки</th>
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
                <td><span class="status ${request.status} event-request-status-badge">${statusLabel(request.status)}</span></td>
                <td><span class="status ${requestMoneyStatus(request)} event-request-status-badge request-money-badge">${statusLabel(requestMoneyStatus(request))}</span></td>
                <td>
                  <div class="inline-actions request-actions-row">
                    ${adminRequestActions(request, "regular")}
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
  return (requests || []).filter((request) => {
    if (["rejected", "cancelled"].includes(request.status)) return false;
    if (request.status === "paid" && requestMoneyStatus(request) === "cash_received") return false;
    return true;
  });
}

function archivedPaymentRequests(requests) {
  return (requests || []).filter((request) => {
    if (["rejected", "cancelled"].includes(request.status)) return true;
    return request.status === "paid" && requestMoneyStatus(request) === "cash_received";
  });
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
  const showRole = user?.role !== "department_head";

  return `
    <span class="user-badge-main">
      <span class="user-badge-line">${name}</span>
      ${showRole ? `<span class="user-badge-role">${roleLabel(user?.role)}</span>` : ""}
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
  document.body.classList.add("login-mode");
  document.body.classList.remove("dashboard-mode");
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
  document.body.classList.remove("login-mode");
  document.body.classList.add("dashboard-mode");
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

function userMonthKey(value) {
  if (!value) return "";
  return String(value).slice(0, 7);
}

function currentCalendarMonthKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function managerDeletedInSelectedMonth(manager) {
  return manager?.role === "manager" && !manager.is_active && userMonthKey(manager.updated_at) === String(state.month || "").slice(0, 7);
}

function canRestoreManagerInSelectedMonth(manager) {
  const monthKey = String(state.month || "").slice(0, 7);
  const monthClosed = state.adminData?.closing?.status === "closed";
  return managerDeletedInSelectedMonth(manager) && monthKey === currentCalendarMonthKey() && !monthClosed;
}

function getOverviewManagers() {
  return (state.users || []).filter((user) => (
    user.role === "manager" && (user.is_active || managerDeletedInSelectedMonth(user))
  ));
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
  return groupedAdminEventsForTable(events || []).filter(eventMatchesAdminFilters);
}

function filteredPaymentRequests(requests, mode = "regular") {
  let list = requests || [];

  if (mode === "archive") {
    list = archivedPaymentRequests(list);
    if (state.paymentStatusFilter !== "all" && state.paymentStatusFilter !== "active") {
      list = list.filter((request) => request.status === state.paymentStatusFilter);
    }
  } else {
    list = activePaymentRequests(list);
    if (state.paymentStatusFilter !== "active" && state.paymentStatusFilter !== "all") {
      list = list.filter((request) => request.status === state.paymentStatusFilter);
    }
  }

  if (state.paymentCustomerFilter && state.paymentCustomerFilter !== "all") {
    list = list.filter((request) => String(paymentRequestClientName(request)) === String(state.paymentCustomerFilter));
  }

  if (state.paymentManagerFilter && state.paymentManagerFilter !== "all") {
    list = list.filter((request) => String(request.manager_name || "") === String(state.paymentManagerFilter));
  }

  return list;
}

function renderAdminTabs() {
  const tabs = [
    ["overview", "Обзор"],
    ["events", "Мероприятия"],
    ["events_archive", "Архив мероприятий"],
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


function renderDepartmentHeadTabs() {
  const tabs = [
    ["overview", "Обзор"],
    ["events", "Мероприятия"],
    ["requests", "Заявки"],
    ["totals", "Итог"],
  ];

  $("adminTabs").classList.remove("hidden");
  $("adminTabs").innerHTML = tabs.map(([key, label]) => `
    <button class="tab-btn ${state.activeDepartmentHeadTab === key ? "active" : ""}" data-dephead-tab="${key}">
      ${label}
    </button>
  `).join("");

  document.querySelectorAll("[data-dephead-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeDepartmentHeadTab = button.getAttribute("data-dephead-tab");
      if (state.activeDepartmentHeadTab === "requests" && state.paymentStatusFilter === "active") {
        state.paymentStatusFilter = "all";
      }
      setLoading(true, "Переключаем вкладку…");
      setTimeout(() => {
        try {
          renderDepartmentDashboard(state.departmentHeadData || {});
        } finally {
          setLoading(false);
        }
      }, 60);
    });
  });
}


function sortManagersByPlanProgress(rows = []) {
  return [...(rows || [])].sort((a, b) => {
    const percentDiff = asNumber(b.completion_percent ?? b.percent) - asNumber(a.completion_percent ?? a.percent);
    if (Math.abs(percentDiff) > 0.0001) return percentDiff;

    const factDiff = asNumber(b.fact_income_amount ?? b.income) - asNumber(a.fact_income_amount ?? a.income);
    if (Math.abs(factDiff) > 0.0001) return factDiff;

    const eventsDiff = asNumber(b.events_count ?? b.eventsCount) - asNumber(a.events_count ?? a.eventsCount);
    if (Math.abs(eventsDiff) > 0.0001) return eventsDiff;

    const aName = String(a.name || a.manager?.name || "");
    const bName = String(b.name || b.manager?.name || "");
    return aName.localeCompare(bName, "ru");
  });
}

function championBadge(rank, percent) {
  return rank === 0 && asNumber(percent) > 0 ? `<em class="manager-champion-badge" title="Чемпион месяца">🏆</em>` : "";
}

function renderDepartmentHeadManagerRows(managers = []) {
  if (!managers.length) return `<div class="empty-state">Активных менеджеров отдела пока нет.</div>`;

  return `
    <section class="department-head-panel">
      <div class="block-title compact-block-title">
        <h3>Менеджеры отдела</h3>
        <span class="muted">${managers.length} чел.</span>
      </div>
      <div class="department-head-manager-list">
        ${sortManagersByPlanProgress(managers).map((manager, index) => {
          const percent = asNumber(manager.completion_percent);
          const eventsCount = Number(manager.events_count || 0);
          return `
            <article class="department-head-manager-row">
              <div class="department-head-manager-main">
                <strong>${escapeHtml(manager.name || "Менеджер")}</strong>
                ${championBadge(index, percent)}
                ${eventsCount > 0 ? `<span class="manager-events-badge" title="Мероприятий">${eventsCount}</span>` : ""}
              </div>
              <div class="department-head-manager-progress">
                <div class="manager-plan-row department-head-plan-row">
                  <span>Факт: ${formatMoney(manager.fact_income_amount)} ₸</span>
                  <span>План: ${formatMoney(manager.plan_amount)} ₸</span>
                  <strong>${percent}%</strong>
                </div>
                ${progressLine(percent)}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `;
}

function renderDepartmentHeadOverview(data) {
  const percent = asNumber(data.completion_percent);
  const calc = data.calculation || {};
  return `
    <section class="manager-plan-panel department-head-plan-panel ${departmentClassByName(data.department_name)}">
      <div>
        <div class="overview-label">План отдела</div>
        <h3>${escapeHtml(data.department_name || "Отдел")}</h3>
      </div>
      <div class="manager-plan-main">
        <div class="manager-plan-row">
          <strong>Факт: ${formatMoney(data.fact_income_amount)} ₸</strong>
          <strong>Цель: ${formatMoney(data.plan_amount)} ₸</strong>
          <strong>${percent}%</strong>
        </div>
        ${progressLine(percent)}
        <div class="muted">Осталось: ${formatMoney(data.remaining_to_plan)} ₸ · расходов: ${formatMoney(data.expenses_amount)} ₸</div>
      </div>
    </section>

    ${renderDepartmentHeadManagerRows(data.managers || [])}
  `;
}

function departmentHeadEventManagerOptions(events = []) {
  return uniqueSortedValues((events || []).map((event) => event.manager_name || managerNameById(event.manager_id)).filter(Boolean));
}

function departmentHeadEventStatusOptions(events = []) {
  return uniqueSortedValues((events || []).map((event) => event.status).filter(Boolean));
}

function departmentHeadEventCustomerOptions(events = []) {
  return uniqueSortedValues((events || []).map((event) => event.client_name).filter(Boolean));
}

function departmentHeadEventMatchesFilters(event) {
  if (state.eventManagerFilter && state.eventManagerFilter !== "all") {
    const managerName = event.manager_name || managerNameById(event.manager_id) || "";
    if (String(managerName) !== String(state.eventManagerFilter)) return false;
  }

  if (state.eventStatusFilter && state.eventStatusFilter !== "all" && event.status !== state.eventStatusFilter) {
    return false;
  }

  if (state.eventCustomerFilter && state.eventCustomerFilter !== "all") {
    if (String(event.client_name || "") !== String(state.eventCustomerFilter)) return false;
  }

  return true;
}

function renderDepartmentHeadEventFilters(events = []) {
  const managerOptions = departmentHeadEventManagerOptions(events);
  const statusOptions = departmentHeadEventStatusOptions(events);
  const customerOptions = departmentHeadEventCustomerOptions(events);

  return `
    <div class="filters-row department-head-filters-row">
      <label class="compact-label">Менеджер
        <select id="depHeadEventManagerFilter">
          ${selectOptions(managerOptions, state.eventManagerFilter, "Все менеджеры")}
        </select>
      </label>
      <label class="compact-label">Статус
        <select id="depHeadEventStatusFilter">
          ${selectOptions(statusOptions.map((status) => ({ value: status, label: statusLabel(status) })), state.eventStatusFilter, "Все статусы")}
        </select>
      </label>
      <label class="compact-label">Заказчик
        <select id="depHeadEventCustomerFilter">
          ${selectOptions(customerOptions, state.eventCustomerFilter, "Все заказчики")}
        </select>
      </label>
    </div>
  `;
}

function renderDepartmentHeadEventsTable(events = []) {
  const sourceEvents = events || [];
  const filteredEvents = sourceEvents.filter(departmentHeadEventMatchesFilters);
  if (!sourceEvents.length) return `<div class="empty-state">Нет мероприятий за выбранный месяц.</div>`;
  const sortedEvents = [...filteredEvents].sort((a, b) => {
    const dateCompare = String(a.event_date || "").localeCompare(String(b.event_date || ""));
    if (dateCompare !== 0) return dateCompare;
    return Number(a.id || 0) - Number(b.id || 0);
  });

  return `
    ${renderDepartmentHeadEventFilters(sourceEvents)}
    <div class="block-title compact-block-title"><h3>Мероприятия отдела</h3><span class="muted">${filteredEvents.length} из ${sourceEvents.length} шт.</span></div>
    ${sortedEvents.length ? `
    <div class="table-wrap admin-events-table-wrap department-head-table-wrap">
      <table class="admin-events-table department-head-events-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Менеджер</th>
            <th>Заказчик</th>
            <th>Мероприятие</th>
            <th>Статус</th>
            <th>Статус денег</th>
            <th>Оборот</th>
            <th>Доход всего</th>
            <th>В план отдела</th>
            <th>Доля</th>
            <th>Заявки</th>
          </tr>
        </thead>
        <tbody>
          ${sortedEvents.map((event) => `
            <tr class="clickable-row admin-event-row ${event.is_shared ? "department-mixed" : departmentClassByName(dataSafeDepartmentName(event))}" data-event-id="${event.id}">
              <td class="nowrap">${formatDateRu(event.event_date) || event.event_date || ""}</td>
              <td>${escapeHtml(event.manager_name || managerNameById(event.manager_id) || "")}</td>
              <td><strong>${escapeHtml(event.client_name || "")}</strong></td>
              <td>${escapeHtml(event.title || "")}${event.is_shared ? `<span class="mini-chip">соавт.</span>` : ""}</td>
              <td><span class="status ${event.status} admin-event-status-badge">${statusLabel(event.status)}</span></td>
              <td><span class="status ${eventMoneyStatus(event)} admin-event-money-badge">${statusLabel(eventMoneyStatus(event))}</span></td>
              <td>${formatMoney(event.external_total)}</td>
              <td>${formatMoney(event.final_company_income)}</td>
              <td><strong>${formatMoney(event.department_income)}</strong></td>
              <td>${formatPercentValue(event.department_share_percent || 0)}%</td>
              <td>${event.active_payment_requests_count ?? event.payment_requests_count ?? 0}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
    ` : `<div class="empty-state">По фильтрам мероприятий нет.</div>`}
  `;
}

function dataSafeDepartmentName(event) {
  return event.department_name || departmentNameById(event.department_id) || "";
}

function departmentHeadRequestCustomerOptions(requests = []) {
  return uniqueSortedValues((requests || []).map((request) => paymentRequestClientName(request)).filter(Boolean));
}

function departmentHeadRequestManagerOptions(requests = []) {
  return uniqueSortedValues((requests || []).map((request) => request.manager_name || paymentRequestManagerName(request)).filter(Boolean));
}

function departmentHeadRequestStatusOptions(requests = []) {
  return uniqueSortedValues((requests || []).map((request) => request.status).filter(Boolean));
}

function departmentHeadRequestMatchesFilters(request) {
  if (state.paymentStatusFilter && state.paymentStatusFilter !== "all" && state.paymentStatusFilter !== "active") {
    if (request.status !== state.paymentStatusFilter) return false;
  }

  if (state.paymentCustomerFilter && state.paymentCustomerFilter !== "all") {
    if (String(paymentRequestClientName(request)) !== String(state.paymentCustomerFilter)) return false;
  }

  if (state.paymentManagerFilter && state.paymentManagerFilter !== "all") {
    const managerName = request.manager_name || paymentRequestManagerName(request) || "";
    if (String(managerName) !== String(state.paymentManagerFilter)) return false;
  }

  return true;
}

function renderDepartmentHeadRequestFilters(requests = []) {
  const statusOptions = departmentHeadRequestStatusOptions(requests);
  const customerOptions = departmentHeadRequestCustomerOptions(requests);
  const managerOptions = departmentHeadRequestManagerOptions(requests);

  return `
    <div class="filters-row department-head-filters-row">
      <label class="compact-label">Статус заявки
        <select id="depHeadRequestStatusFilter">
          ${selectOptions(statusOptions.map((status) => ({ value: status, label: statusLabel(status) })), state.paymentStatusFilter === "active" ? "all" : state.paymentStatusFilter, "Все статусы")}
        </select>
      </label>
      <label class="compact-label">Заказчик
        <select id="depHeadRequestCustomerFilter">
          ${selectOptions(customerOptions, state.paymentCustomerFilter, "Все заказчики")}
        </select>
      </label>
      <label class="compact-label">Менеджер
        <select id="depHeadRequestManagerFilter">
          ${selectOptions(managerOptions, state.paymentManagerFilter, "Все менеджеры")}
        </select>
      </label>
    </div>
  `;
}

function renderDepartmentHeadRequestsTable(requests = []) {
  const sourceRequests = requests || [];
  const filtered = sourceRequests.filter(departmentHeadRequestMatchesFilters);
  if (!sourceRequests.length) return `<div class="empty-state">Заявок отдела нет.</div>`;
  return `
    ${renderDepartmentHeadRequestFilters(sourceRequests)}
    <div class="block-title compact-block-title">
      <h3>Заявки отдела</h3>
      <span class="muted">${filtered.length} из ${sourceRequests.length} шт.</span>
    </div>
    ${filtered.length ? `
    <div class="table-wrap department-head-table-wrap">
      <table class="department-head-requests-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Менеджер</th>
            <th>Заказчик</th>
            <th>Мероприятие</th>
            <th>Позиция</th>
            <th>Сумма</th>
            <th>Способ</th>
            <th>Оплата</th>
            <th>Деньги</th>
          </tr>
        </thead>
        <tbody>
          ${filtered.map((request) => `
            <tr>
              <td>${formatDateRu(paymentRequestDateValue(request)) || paymentRequestDateValue(request) || ""}</td>
              <td>${escapeHtml(request.manager_name || "")}</td>
              <td>${escapeHtml(paymentRequestClientName(request))}</td>
              <td>${escapeHtml(paymentRequestEventTitle(request))}</td>
              <td>${escapeHtml(request.position || request.item_name_snapshot || "")}</td>
              <td><strong>${formatMoney(request.amount_requested)}</strong></td>
              <td>${paymentMethodLabel(request.payment_method)}</td>
              <td><span class="status ${request.status} request-status-badge">${statusLabel(request.status)}</span></td>
              <td><span class="status ${requestMoneyStatus(request)} request-money-badge">${statusLabel(requestMoneyStatus(request))}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
    ` : `<div class="empty-state">По фильтрам заявок нет.</div>`}
  `;
}

function renderDepartmentHeadExpensesTable(expenses = []) {
  if (!expenses.length) return `<div class="empty-state compact-empty-state">Расходов по этому отделу пока нет.</div>`;
  return `
    <div class="table-wrap department-head-expenses-wrap compact-expenses-wrap">
      <table class="department-head-expenses-table compact-expenses-table">
        <thead>
          <tr>
            <th>Расход</th>
            <th>Тип</th>
            <th>Сумма отдела</th>
            <th>Общая сумма</th>
            <th>Комментарий</th>
          </tr>
        </thead>
        <tbody>
          ${expenses.map((expense) => `
            <tr>
              <td><strong>${escapeHtml(expense.title || "")}</strong></td>
              <td>${escapeHtml(expense.allocation_label || "")}</td>
              <td><strong>${formatMoney(expense.department_amount)}</strong></td>
              <td>${formatMoney(expense.total_amount)}</td>
              <td>${escapeHtml(expense.comment || "")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderDepartmentHeadExpensesModalContent(data = {}) {
  const expenses = data.expenses || [];
  const amount = data.calculation?.expense_amount ?? data.expenses_amount ?? 0;
  return `
    <div class="department-expenses-modal-content">
      <div class="department-expenses-modal-summary">
        <span>${escapeHtml(data.department_name || "Отдел")}</span>
        <strong>${formatMoney(amount)} ₸</strong>
        <em>${expenses.length} расход${expenses.length === 1 ? "" : "ов"}</em>
      </div>
      ${renderDepartmentHeadExpensesTable(expenses)}
    </div>
  `;
}

function closeDepartmentHeadExpensesModal() {
  const backdrop = document.getElementById("departmentExpensesModalBackdrop");
  if (backdrop) backdrop.classList.add("hidden");
}

function openDepartmentHeadExpensesModal() {
  const backdrop = document.getElementById("departmentExpensesModalBackdrop");
  const title = document.getElementById("departmentExpensesModalTitle");
  const content = document.getElementById("departmentExpensesModalContent");
  if (!backdrop || !content) return;

  const data = state.departmentHeadData || {};
  if (title) title.textContent = `Расходы · ${data.department_name || "отдел"}`;
  content.innerHTML = renderDepartmentHeadExpensesModalContent(data);
  backdrop.classList.remove("hidden");
}

function attachDepartmentHeadExpensesModal() {
  document.querySelectorAll("[data-open-department-expenses]").forEach((button) => {
    button.addEventListener("click", openDepartmentHeadExpensesModal);
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openDepartmentHeadExpensesModal();
      }
    });
  });

  const closeBtn = document.getElementById("departmentExpensesModalCloseBtn");
  if (closeBtn && !closeBtn.dataset.bound) {
    closeBtn.dataset.bound = "1";
    closeBtn.addEventListener("click", closeDepartmentHeadExpensesModal);
  }

  const backdrop = document.getElementById("departmentExpensesModalBackdrop");
  if (backdrop && !backdrop.dataset.bound) {
    backdrop.dataset.bound = "1";
    backdrop.addEventListener("click", (event) => {
      if (event.target === backdrop) closeDepartmentHeadExpensesModal();
    });
  }
}

function departmentHeadClickableExpenseMetric(value, count) {
  return `
    <button class="card metric department-expense-summary-card" type="button" data-open-department-expenses aria-label="Открыть расходы отдела">
      <div class="label">Расходы</div>
      <div class="value">${value}</div>
      <div class="metric-hint">${count} шт. · открыть</div>
    </button>
  `;
}

function renderDepartmentHeadTotals(data) {
  const calc = data.calculation || {};
  const expensesCount = (data.expenses || []).length;
  return `
    <section class="closing-mini-section department-head-total-section">
      <div class="closing-section-head">
        <h4>Итог отдела</h4>
        <span>актуальная калькуляция</span>
      </div>
      <div class="closing-calc-grid department-head-calc-grid">
        ${metric("План", formatMoney(calc.plan_amount || data.plan_amount || 0))}
        ${metric("Факт", formatMoney(calc.income_amount || data.fact_income_amount || 0))}
        ${metric("Выполнение", `${calc.completion_percent || data.completion_percent || 0}%`)}
        ${departmentHeadClickableExpenseMetric(formatMoney(calc.expense_amount || data.expenses_amount || 0), expensesCount)}
        ${metric("% главы", `${calc.head_percent || 0}%`)}
        ${metric("ЗП главы", formatMoney(calc.head_salary || 0))}
      </div>
    </section>
  `;
}


function adminEventDepartmentToneClass(event) {
  const ids = [...new Set((event.department_ids || [event.department_id]).map((id) => Number(id)).filter(Boolean))];

  if (ids.length > 1) {
    const classes = ids.map((id) => departmentClassById(id));
    if (classes.includes("department-sanzhar") && classes.includes("department-raufal")) {
      return "department-mixed-sanzhar-raufal";
    }
    return "department-mixed";
  }

  return departmentClassById(ids[0] || event.department_id);
}


function renderEventsTable(events, allowClick = false) {
  if (!events || !events.length) return `<div class="empty-state">Нет мероприятий за выбранный месяц.</div>`;

  const sortedEvents = [...events].sort((a, b) => {
    const dateCompare = String(a.event_date || "").localeCompare(String(b.event_date || ""));
    if (dateCompare !== 0) return dateCompare;
    return Number(a.id || 0) - Number(b.id || 0);
  });

  return `
    <div class="table-wrap admin-events-table-wrap">
      <table class="admin-events-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Менеджер</th>
            <th>Заказчик</th>
            <th>Мероприятие</th>
            <th>Оплата</th>
            <th>Статус</th>
            <th>Статус денег</th>
            <th>Оборот</th>
            <th>Доход</th>
            <th>ЗП менеджера</th>
            <th>Заявки</th>
          </tr>
        </thead>
        <tbody>
          ${sortedEvents.map((event) => `
            <tr class="${allowClick ? "clickable-row" : ""} admin-event-row ${adminEventDepartmentToneClass(event)}" ${allowClick ? `data-event-id="${event.id}"` : ""}>
              <td class="nowrap">${formatDateRu(event.event_date) || event.event_date || ""}</td>
              <td>${event.manager_name || managerNameById(event.manager_id) || ""}</td>
              <td><strong>${event.client_name || ""}</strong></td>
              <td>${event.title || ""}</td>
              <td>${calcTypeLabel(event.client_calc_type)}</td>
              <td><span class="status ${event.status} admin-event-status-badge">${statusLabel(event.status)}</span></td>
              <td><span class="status ${eventMoneyStatus(event)} admin-event-money-badge">${statusLabel(eventMoneyStatus(event))}</span></td>
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
  const customers = eventCustomerFilterOptions(events || []);

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
          ${statuses.map((status) => `<option value="${status}" ${state.eventStatusFilter === status ? "selected" : ""}>${statusLabel(status)}</option>`).join("")}
        </select>
      </label>

      <label class="compact-label">Заказчик
        <select id="eventCustomerFilter">
          ${selectOptions(customers, state.eventCustomerFilter, "Все заказчики")}
        </select>
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

function paymentCustomerFilterOptions(requests) {
  const names = [...new Set((requests || []).map((request) => paymentRequestClientName(request)).filter(Boolean))];
  return names.sort((a, b) => String(a).localeCompare(String(b), "ru"));
}

function paymentManagerFilterOptions(requests, mode = "regular") {
  const base = mode === "archive" ? archivedPaymentRequests(requests) : activePaymentRequests(requests);
  return uniqueSortedValues(base.map((request) => managerNameForRequest(request)));
}

function selectOptions(values, selectedValue, allLabel) {
  return `
    <option value="all" ${selectedValue === "all" || !selectedValue ? "selected" : ""}>${allLabel}</option>
    ${values.map((item) => {
      const value = typeof item === "object" && item !== null ? item.value : item;
      const label = typeof item === "object" && item !== null ? item.label : item;
      return `<option value="${escapeHtml(value)}" ${String(selectedValue) === String(value) ? "selected" : ""}>${escapeHtml(label)}</option>`;
    }).join("")}
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
  return !["paid", "rejected"].includes(request.status);
}

function adminRequestActions(request, mode = "regular") {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return "";

  const status = request.status;
  const moneyStatus = requestMoneyStatus(request);
  const buttons = [];

  if (mode === "archive") {
    if (status === "paid" && moneyStatus === "cash_received") {
      buttons.push(`<button class="small danger" data-refund-request="${request.id}">Вернуть</button>`);
    }
    return buttons.join("");
  }

  if (status !== "paid" && !["rejected", "cancelled"].includes(status)) {
    buttons.push(`<button class="small" data-set-request-status="${request.id}:paid">Оплачено</button>`);
  }

  if (moneyStatus !== "cash_received" && !["rejected", "cancelled"].includes(status)) {
    buttons.push(`<button class="small secondary" data-set-request-money-status="${request.id}:cash_received">Деньги в кассе</button>`);
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

function removeEventModalActions() {
  const oldActions = document.getElementById("eventModalActions");
  if (oldActions) oldActions.remove();
}

function resetEventModalModes() {
  const eventBackdrop = $("eventModalBackdrop");
  const plansBackdrop = $("plansModalBackdrop");

  if (plansBackdrop) {
    plansBackdrop.classList.remove("manager-payments-modal");
  }

  if (eventBackdrop) {
    eventBackdrop.classList.remove(
      "manager-payments-modal",
      "manager-create-modal",
      "payment-modal-mode",
      "pin-modal-mode",
      "profile-modal-mode",
      "manager-requests-modal-mode",
      "admin-event-edit-mode"
    );
  }

  state.adminEventEditModeId = null;
  removeEventModalActions();
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

  resetEventModalModes();
  backdrop.classList.add("manager-payments-modal");
  // managerPaymentsModalClass_v03715

  await refreshManagerPaymentRequestsForEvent(eventId);

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



function paymentRequestDateValue(request) {
  return request?.created_at || request?.created_date || request?.date_created || request?.request_date || request?.createdAt || request?.date || "";
}

function paymentRequestClientName(request) {
  return request?.client_name || request?.customer_name || request?.event_client_name || request?.client || request?.customer || request?.company_name || "";
}

function paymentRequestManagerName(request) {
  return request?.manager_name || managerNameById(request?.manager_id) || managerNameForRequest(request) || "";
}

function paymentRequestEventTitle(request) {
  return request?.event_title || request?.title || request?.event_name || request?.event || "";
}

function renderPaymentRequestsTable(requests, title = "Заявки", mode = "regular") {
  const filtered = filteredPaymentRequests(requests || [], mode);

  return `
    ${renderPaymentFilters(requests || [], mode)}

    <div class="block-title">
      <h3>${title}</h3>
      <span class="muted">${filtered.length} шт.</span>
    </div>

    ${filtered.length ? `
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Дата</th>
              <th>Менеджер</th>
              <th>Заказчик</th>
              <th>Мероприятие</th>
              <th>Позиция</th>
              <th>Сумма</th>
              <th>Способ</th>
              <th>Статус оплаты</th>
              <th>Статус денег</th>
              <th>Кнопки</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.map((request) => `
              <tr>
                <td>${formatDateRu(paymentRequestDateValue(request)) || paymentRequestDateValue(request) || ""}</td>
                <td>${paymentRequestManagerName(request)}</td>
                <td>${paymentRequestClientName(request)}</td>
                <td>${paymentRequestEventTitle(request)}</td>
                <td>${request.position || request.item_name_snapshot || ""}</td>
                <td><strong>${formatMoney(request.amount_requested)}</strong></td>
                <td>${paymentMethodLabel(request.payment_method)}</td>
                <td><span class="status ${request.status} request-status-badge">${statusLabel(request.status)}</span></td>
                <td><span class="status ${requestMoneyStatus(request)} request-money-badge">${statusLabel(requestMoneyStatus(request))}</span></td>
                <td>
                  <div class="inline-actions request-actions-row">
                    ${adminRequestActions(request, mode)}
                    ${canManagerCancelRequest(request) ? `<button class="small danger" data-cancel-request="${request.id}">Отменить</button>` : ""}
                  </div>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    ` : `<div class="empty-state">Заявок нет.</div>`}
  `;
}

function attachDepartmentHeadFilters() {
  const rerender = () => renderDepartmentDashboard(state.departmentHeadData || {});

  const eventManager = document.getElementById("depHeadEventManagerFilter");
  if (eventManager) eventManager.addEventListener("change", (event) => {
    state.eventManagerFilter = event.target.value;
    rerender();
  });

  const eventStatus = document.getElementById("depHeadEventStatusFilter");
  if (eventStatus) eventStatus.addEventListener("change", (event) => {
    state.eventStatusFilter = event.target.value;
    rerender();
  });

  const eventCustomer = document.getElementById("depHeadEventCustomerFilter");
  if (eventCustomer) eventCustomer.addEventListener("change", (event) => {
    state.eventCustomerFilter = event.target.value;
    rerender();
  });

  const requestStatus = document.getElementById("depHeadRequestStatusFilter");
  if (requestStatus) requestStatus.addEventListener("change", (event) => {
    state.paymentStatusFilter = event.target.value;
    rerender();
  });

  const requestCustomer = document.getElementById("depHeadRequestCustomerFilter");
  if (requestCustomer) requestCustomer.addEventListener("change", (event) => {
    state.paymentCustomerFilter = event.target.value;
    rerender();
  });

  const requestManager = document.getElementById("depHeadRequestManagerFilter");
  if (requestManager) requestManager.addEventListener("change", (event) => {
    state.paymentManagerFilter = event.target.value;
    rerender();
  });
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
    eventDepartment.addEventListener("change", (event) => {
      state.eventDepartmentFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const eventManager = document.getElementById("eventManagerFilter");
  if (eventManager) {
    eventManager.addEventListener("change", (event) => {
      state.eventManagerFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const eventStatus = document.getElementById("eventStatusFilter");
  if (eventStatus) {
    eventStatus.addEventListener("change", (event) => {
      state.eventStatusFilter = event.target.value;
      renderAdminDashboard(state.adminData);
    });
  }

  const eventCustomer = document.getElementById("eventCustomerFilter");
  if (eventCustomer) {
    eventCustomer.addEventListener("change", (event) => {
      state.eventCustomerFilter = event.target.value;
      renderAdminDashboard(state.adminData);
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

  document.querySelectorAll("[data-set-request-money-status]").forEach((button) => {
    button.addEventListener("click", async () => {
      const raw = button.getAttribute("data-set-request-money-status");
      const [id, money_status] = raw.split(":");

      if (!confirm(`Заявку #${id} отметить как “Деньги в кассе”?`)) return;

      try {
        await api(`/payment-requests/${id}/money-status`, {
          method: "PATCH",
          body: JSON.stringify({ money_status }),
        });
        await withLoading(loadDashboard, "Обновляем данные…");
      } catch (error) {
        alert(error.message);
      }
    });
  });

  document.querySelectorAll("[data-refund-request]").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = button.getAttribute("data-refund-request");

      if (!confirm(`Вернуть деньги по заявке #${id}? Статус оплаты станет “Отменено”, статус денег — “Отменено”.`)) return;

      try {
        await api(`/payment-requests/${id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status: "rejected" }),
        });
        await api(`/payment-requests/${id}/money-status`, {
          method: "PATCH",
          body: JSON.stringify({ money_status: "cancelled" }),
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


function customerVatTopAmount(summary) {
  return asNumber(
    summary?.vat_to_pay ??
    summary?.customer_vat_amount ??
    summary?.vat_customer_amount ??
    0
  );
}

function customerTaxesTopAmount(summary) {
  // Для верхней карточки "Налоги ... к уплате" нужна сумма именно к уплате:
  // внутренние налоги минус доступные вычеты.
  const grossTaxes = asNumber(summary?.taxes_total ?? (asNumber(summary?.internal_tax_amount) + asNumber(summary?.simplified_bank_tax_amount)));
  const deductions = asNumber(summary?.deductions_total ?? summary?.tax_deductions_total ?? 0);
  return Math.max(0, Math.round(grossTaxes - deductions));
}

function customerTurnoverAmount(summary) {
  return asNumber(summary?.turnover_with_vat ?? summary?.external_total ?? 0);
}

function estimateExternalSubtotal(items) {
  return (items || []).reduce((sum, item) => sum + asNumber(item.external_amount), 0);
}

function customerAgencyCommissionTopAmount(event, summary, items, taxesAmount, vatAmount) {
  const explicitAmount = asNumber(
    summary?.agency_commission_amount ??
    summary?.agency_commission_total ??
    summary?.customer_agency_commission_amount ??
    event?.agency_commission_amount_value ??
    0
  );
  if (explicitAmount > 0) return explicitAmount;

  const percent = asNumber(event?.agency_commission_amount ?? event?.agency_commission_percent ?? summary?.agency_commission_percent ?? 0);
  if (percent > 0 && percent <= 100) {
    const subtotal = estimateExternalSubtotal(items);
    return Math.round(subtotal * percent / 100);
  }

  const turnover = customerTurnoverAmount(summary);
  const subtotal = estimateExternalSubtotal(items);
  return Math.max(0, Math.round(turnover - subtotal - asNumber(taxesAmount) - asNumber(vatAmount)));
}



function customerEstimateBankTaxTopAmount(summary) {
  // В строке сметы "Налоги" показываем только банковские/налоговые платежи,
  // которые добавляются сверху заказчику при Упрощенке.
  return asNumber(summary?.simplified_bank_tax_amount ?? summary?.customer_bank_tax_amount ?? 0);
}

function customerEstimateVatTopAmount(event, summary, items, taxesAmount, agencyAmount) {
  // В строке сметы "НДС" нужен НДС по смете — то есть та часть,
  // которая добивает позиции + комиссия + налоги до оборота.
  // Верхняя карточка "НДС" остаётся отдельной: НДС к оплате / с учётом вычетов.
  const explicit = asNumber(
    summary?.estimate_vat_amount ??
    summary?.customer_vat_top_amount ??
    summary?.customer_vat_amount ??
    0
  );
  if (explicit > 0) return explicit;

  const turnover = customerTurnoverAmount(summary);
  const subtotal = estimateExternalSubtotal(items);
  return Math.max(0, Math.round(turnover - subtotal - asNumber(agencyAmount) - asNumber(taxesAmount)));
}


function adminEstimateTopRows(event, summary, items, taxesAmount, vatAmount) {
  const bankTaxTopAmount = customerEstimateBankTaxTopAmount(summary);
  const agencyAmount = customerAgencyCommissionTopAmount(event, summary, items, bankTaxTopAmount, 0);
  const estimateVatAmount = customerEstimateVatTopAmount(event, summary, items, bankTaxTopAmount, agencyAmount);
  const rows = [];

  if (agencyAmount > 0) {
    rows.push({ name: "Комиссия", amount: agencyAmount });
  }

  if (asNumber(bankTaxTopAmount) > 0) {
    rows.push({ name: "Налоги", amount: bankTaxTopAmount });
  }

  if (asNumber(estimateVatAmount) > 0) {
    rows.push({ name: "НДС", amount: estimateVatAmount });
  }

  return rows.map((row) => `
    <tr class="estimate-top-charge-row">
      <td><strong>${row.name}</strong></td>
      <td>${formatMoney(row.amount)}</td>
      <td>0</td>
      <td class="paid-col">0</td>
      <td class="commission-col">0</td>
      <td class="vat-col">0</td>
      <td class="deduction-col">0</td>
      <td class="method-col">—</td>
    </tr>
  `).join("");
}



function canAdminDeleteEvent(event, requests = []) {
  if (!event || !["draft", "revision"].includes(event.status)) return false;
  if (eventMoneyStatus(event) === "cash_received") return false;
  return !(requests || []).some((request) => !["rejected", "cancelled"].includes(request.status));
}

function adminEventModalActions(event, requests = []) {
  const normalizedRequests = requests || [];
  const deleteStatusAllowed = ["draft", "revision"].includes(event?.status);
  const hasActivePayments = normalizedRequests.some((request) => !["rejected", "cancelled"].includes(request.status));
  const eventCashReceived = eventMoneyStatus(event) === "cash_received";
  const hasCashReceivedMoney = eventCashReceived || normalizedRequests.some((request) => requestMoneyStatus(request) === "cash_received");
  const deleteDisabledReason = eventCashReceived
    ? "Нельзя удалить: деньги уже в кассе"
    : hasActivePayments
      ? "Нельзя удалить: есть активные оплаты"
      : "";
  const canDelete = deleteStatusAllowed && !hasActivePayments && !eventCashReceived;

  const showAccept = ["review", "accepted"].includes(event?.status);
  const canAccept = event?.status === "review";
  const canRevision = event?.status === "review" || (event?.status === "accepted" && !eventCashReceived);
  const canReturnToWork = ["accepted"].includes(event?.status) && eventCashReceived;
  const canAdminEdit = event?.status !== "cancelled";

  const showCashReceived = !["cancelled"].includes(event?.status);
  const canCashReceived = showCashReceived && !hasCashReceivedMoney;

  return `
    <div class="event-modal-actions">
      ${canAdminEdit ? `<button class="event-action-btn event-edit-btn" data-admin-event-edit="${event.id}" title="Редактировать мероприятие">✏️</button>` : ""}
      ${deleteStatusAllowed ? `<button class="danger-btn event-action-btn event-delete-btn ${canDelete ? "" : "is-disabled"}" ${canDelete ? "" : `disabled title="${deleteDisabledReason}"`} data-admin-event-delete="${event.id}" ${eventMoneyStatus(event) === "cash_received" ? 'disabled title="Нельзя удалить: деньги уже в кассе"' : ""}>Удалить</button>` : ""}
      ${canRevision ? `<button class="event-action-btn event-revision-btn" data-admin-event-revision="${event.id}">На доработку</button>` : ""}
      ${canReturnToWork ? `<button class="event-action-btn event-return-btn" data-admin-event-revision="${event.id}">Вернуть в работу</button>` : ""}
      ${showAccept ? `<button class="event-action-btn event-accept-btn ${canAccept ? "" : "is-disabled"}" ${canAccept ? "" : "disabled title=\"Мероприятие уже принято\""} data-admin-event-accept="${event.id}">Принять</button>` : ""}
      ${showCashReceived ? `<button class="event-action-btn event-cash-btn ${canCashReceived ? "" : "is-disabled"}" ${canCashReceived ? "" : `disabled title="Деньги уже в кассе"`} data-admin-event-cash-received="${event.id}">Деньги в кассе</button>` : ""}
    </div>
  `;
}

function installAdminEventModalActions(event, requests = []) {
  const closeBtn = $("eventModalCloseBtn");
  if (!closeBtn) return;

  removeEventModalActions();

  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return;
  if ($("eventModalBackdrop")?.classList.contains("payment-modal-mode")) return;

  const holder = document.createElement("div");
  holder.id = "eventModalActions";
  holder.innerHTML = adminEventModalActions(event, requests);

  closeBtn.parentElement.insertBefore(holder, closeBtn);

  const editBtn = holder.querySelector("[data-admin-event-edit]");
  if (editBtn) {
    editBtn.addEventListener("click", async (clickEvent) => {
      clickEvent.stopPropagation();
      await openAdminEventEditMode(event.id);
    });
  }

  const deleteBtn = holder.querySelector("[data-admin-event-delete]");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", async (clickEvent) => {
      clickEvent.stopPropagation();
      if (deleteBtn.disabled || deleteBtn.classList.contains("is-disabled")) return;
      if (!confirm("Удалить мероприятие?")) return;

      await api(`/events/${event.id}`, { method: "DELETE" });
      $("eventModalBackdrop").classList.add("hidden");
      await loadDashboard();
    });
  }

  const revisionBtn = holder.querySelector("[data-admin-event-revision]");
  if (revisionBtn) {
    revisionBtn.addEventListener("click", async (clickEvent) => {
      clickEvent.stopPropagation();
      await api(`/events/${event.id}/revision`, { method: "POST" });
      if (eventIsMoneyArchive(event)) {
        state.activeAdminTab = "events";
      }
      await openEventModal(event.id);
      await loadDashboard();
    });
  }

  const acceptBtn = holder.querySelector("[data-admin-event-accept]");
  if (acceptBtn) {
    acceptBtn.addEventListener("click", async (clickEvent) => {
      clickEvent.stopPropagation();
      if (acceptBtn.disabled || acceptBtn.classList.contains("is-disabled")) return;
      await api(`/events/${event.id}/accept`, { method: "POST" });
      await openEventModal(event.id);
      await loadDashboard();
    });
  }

  const cashBtn = holder.querySelector("[data-admin-event-cash-received]");
  if (cashBtn) {
    cashBtn.addEventListener("click", async (clickEvent) => {
      clickEvent.stopPropagation();
      if (cashBtn.disabled || cashBtn.classList.contains("is-disabled")) return;
      if (!confirm("Отметить все оплаты мероприятия как “Деньги в кассе”?")) return;

      await api(`/events/${event.id}/cash-received`, { method: "POST" });
      await openEventModal(event.id);
      await loadDashboard();
    });
  }
}


async function openAdminEventEditMode(eventId) {
  resetEventModalModes();

  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

  backdrop.classList.add("admin-event-edit-mode");
  backdrop.classList.remove("hidden");
  title.textContent = `Редактирование мероприятия #${eventId}`;
  content.innerHTML = `<div class="empty-state">Загрузка редактора...</div>`;

  state.adminEventEditModeId = Number(eventId);
  state.selectedManagerEventId = Number(eventId);
  state.managerEstimateTab = "internal";
  delete state.managerDraftEventsById[String(eventId)];
  delete state.managerDraftItemsByEventId[String(eventId)];
  delete state.managerDraftDeletedByEventId[String(eventId)];

  try {
    const [event, items, summary, requests] = await Promise.all([
      api(`/events/${eventId}`),
      api(`/events/${eventId}/items`),
      api(`/events/${eventId}/summary`),
      api(`/events/${eventId}/payment-requests`),
    ]);

    // В админском редакторе кнопки удаления/блокировки способов оплаты
    // должны знать о заявках мероприятия. Иначе UI разрешал удалить строку,
    // но backend потом отклонял DELETE из-за активных заявок, и весь save падал.
    state.managerPaymentRequests = requests || [];

    const draftEvent = getDraftEvent(event);
    state.currentManagerEvent = draftEvent;
    const draftItems = getDraftItems(eventId, items || []);
    const previewSummary = calculateDraftSummaryPreview(draftItems, draftEvent, summary);
    state.currentManagerSummary = previewSummary;
    state.currentManagerItems = draftItems;

    title.textContent = `✏️ ${event.client_name || "Без заказчика"} · ${event.title || "Без названия"}`;
    content.innerHTML = renderManagerEventCard(draftEvent, draftItems, previewSummary);
    attachManagerCreateWorkspaceActions();
    attachDraftEventInputs(eventId);
    attachDraftInputs(eventId);
  } catch (error) {
    content.innerHTML = `<div class="error">${error.message || "Не удалось открыть редактирование"}</div>`;
  }
}

async function closeAdminEventEditMode(eventId, reloadModal = true) {
  const key = String(eventId || state.adminEventEditModeId || "");
  if (key) {
    delete state.managerDraftEventsById[key];
    delete state.managerDraftItemsByEventId[key];
    delete state.managerDraftDeletedByEventId[key];
  }
  state.adminEventEditModeId = null;
  $("eventModalBackdrop")?.classList.remove("admin-event-edit-mode");
  if (reloadModal && eventId) {
    await openEventModal(eventId);
  }
}

async function openEventModal(eventId) {
  resetEventModalModes();
  // openEventModal_resetSharedChrome_v03715

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
    const taxesAmount = customerTaxesTopAmount(summary);
    const vatAmount = customerVatTopAmount(summary);
    const managerSalary = asNumber(summary.manager_salary);

    $("eventModalContent").innerHTML = `
      <div class="grid cards modal-metric-cards">
        ${metric("Оборот", formatMoney(customerTurnoverAmount(summary)))}
        ${metric(`Налоги ${taxPercentLabelForEvent(event, summary)} к уплате`, formatMoney(taxesAmount))}
        ${metric("НДС к уплате", formatMoney(vatAmount))}
        <div class="card metric manager-salary-metric">
          <div class="label">Менеджер 21%</div>
          <div class="value">${formatMoney(managerSalary)}</div>
        </div>
        <div class="card metric income-metric">
          <div class="label">Доход компании</div>
          <div class="value">${formatMoney(summary.final_company_income)}</div>
        </div>
      </div>

      <div class="divider"></div>

      <h3>Смета</h3>
      <div class="table-wrap estimate-table-wrap">
        <table class="estimate-table event-modal-estimate-table">
          <colgroup>
            <col class="position-col" />
            <col class="amount-col" />
            <col class="amount-col" />
            <col class="amount-col" />
            <col class="commission-col" />
            <col class="vat-col" />
            <col class="deduction-col" />
            <col class="method-col" />
          </colgroup>
          <thead>
            <tr>
              <th>Позиция</th><th>Смета</th><th>Факт</th><th class="paid-col">Оплата</th><th class="commission-col">Комиссия</th><th class="vat-col">НДС</th><th class="deduction-col">Вычеты</th><th class="method-col">Способ</th>
            </tr>
          </thead>
          <tbody>
            ${sortedItems.map((item) => `
              <tr>
                <td><strong>${item.external_name}</strong></td>
                <td>${formatMoney(item.external_amount)}</td>
                <td>${formatMoney(item.amount_fact)}</td>
                <td class="paid-col">${formatMoney(item.paid_amount)}</td>
                <td class="commission-col">${formatMoney(internalCommissionValue(item))}</td>
                <td class="vat-col">${formatMoney(itemVatVisible(item))}</td>
                <td class="deduction-col">${formatMoney(itemDeductionVisible(item))}</td>
                <td class="method-col">${paymentMethodLabel(item.payment_method)}</td>
              </tr>
            `).join("")}
            ${adminEstimateTopRows(event, summary, sortedItems, taxesAmount, vatAmount)}
          </tbody>
        </table>
      </div>

      <div id="eventModalRequestsSection">
        ${renderEventPaymentRequestsTable(requests || [], "all")}
      </div>
    `;

    installAdminEventModalActions(event, requests || []);
    attachPaymentRequestActions();
    attachEventModalRequestFilter(requests || []);
  } catch (error) {
    $("eventModalContent").innerHTML = `<div class="error">${error.message}</div>`;
  }
}

function renderAdminOverview(data) {
  const managers = getOverviewManagers();

  const managerStats = managers.map((manager) => {
    const events = (data.events || []).filter((event) => Number(event.manager_id) === Number(manager.id));
    const eventIds = new Set(events.map((event) => Number(event.id)).filter(Boolean));
    const eventsCount = eventIds.size;
    const income = events.reduce((sum, event) => sum + asNumber(event.final_company_income), 0);
    const plan = asNumber(data.manager_personal_plan_amount);
    const percent = plan > 0 ? Math.round((income / plan) * 10000) / 100 : 0;
    const isInactive = !manager.is_active;
    const canRestore = canRestoreManagerInSelectedMonth(manager);

    return {
      manager,
      income,
      plan,
      percent,
      eventsCount,
      isInactive,
      canRestore,
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
        const depManagers = sortManagersByPlanProgress(managerStats.filter((row) => Number(row.departmentId) === Number(dep.department_id)));

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
              ${depManagers.length ? depManagers.map((row, index) => `
                <div class="manager-progress-row ${row.isInactive ? "is-inactive" : ""}">
                  <div class="manager-progress-main">
                    <strong class="manager-progress-name">
                      <span>${escapeHtml(row.manager.name)}</span>
                      ${championBadge(index, row.percent)}
                      ${row.eventsCount ? `<em class="manager-events-count-badge">${row.eventsCount}</em>` : ""}
                      ${row.isInactive ? `<em class="manager-inactive-badge">до конца месяца</em>` : ""}
                    </strong>
                    <span>${formatMoney(row.income)} ₸ · ${row.percent}%</span>
                  </div>
                  <div class="manager-progress-bar">
                    ${progressLine(row.percent)}
                  </div>
                  ${row.isInactive ? `
                    ${row.canRestore ? `
                      <button class="manager-restore-btn" data-restore-manager-id="${row.manager.id}" data-restore-manager-name="${escapeHtml(row.manager.name)}" title="Восстановить менеджера" type="button">↺</button>
                    ` : `<span class="manager-action-placeholder" title="Срок восстановления прошёл">—</span>`}
                  ` : `
                    <button class="manager-delete-btn" data-delete-manager-id="${row.manager.id}" data-delete-manager-name="${escapeHtml(row.manager.name)}" title="Удалить менеджера" type="button">×</button>
                  `}
                </div>
              `).join("") : `<div class="empty-state">Менеджеров в отделе пока нет.</div>`}
            </div>
          </article>
        `;
      }).join("")}
    </section>
  `;
}

function groupedAdminEventsForTable(events) {
  const groups = new Map();

  [...(events || [])].forEach((event) => {
    const key = String(event.id);
    if (!groups.has(key)) {
      groups.set(key, {
        ...event,
        manager_names: [],
        manager_ids: [],
        department_ids: [],
        final_company_income: 0,
        manager_salary: 0,
        payment_requests_count: event.payment_requests_count ?? 0,
        active_payment_requests_count: event.active_payment_requests_count ?? 0,
      });
    }

    const group = groups.get(key);
    const managerName = event.manager_name || managerNameById(event.manager_id) || "";
    const managerId = Number(event.manager_id || 0);
    const departmentId = Number(event.department_id || 0);

    if (managerName && !group.manager_names.includes(managerName)) group.manager_names.push(managerName);
    if (managerId && !group.manager_ids.includes(managerId)) group.manager_ids.push(managerId);
    if (departmentId && !group.department_ids.includes(departmentId)) group.department_ids.push(departmentId);

    group.final_company_income += asNumber(event.final_company_income);
    group.manager_salary += asNumber(event.manager_salary);
    group.payment_requests_count = Math.max(asNumber(group.payment_requests_count), asNumber(event.payment_requests_count));
    group.active_payment_requests_count = Math.max(asNumber(group.active_payment_requests_count), asNumber(event.active_payment_requests_count));
  });

  return [...groups.values()].map((group) => {
    const selectedDepartment = state.eventDepartmentFilter !== "all"
      ? Number(state.eventDepartmentFilter)
      : (group.department_ids[0] || group.department_id);

    return {
      ...group,
      manager_name: group.manager_names.join(" / "),
      manager_id: group.manager_ids[0] || group.manager_id,
      department_id: selectedDepartment,
    };
  }).sort((a, b) => {
    const dateCompare = String(a.event_date || "").localeCompare(String(b.event_date || ""));
    if (dateCompare !== 0) return dateCompare;
    return Number(a.id || 0) - Number(b.id || 0);
  });
}


function eventCustomerFilterOptions(events) {
  const grouped = groupedAdminEventsForTable(events || []);
  return uniqueSortedValues(grouped.map((event) => event.client_name));
}

function eventMatchesAdminFilters(event) {
  if (state.eventDepartmentFilter !== "all") {
    const departmentIds = event.department_ids || [event.department_id];
    if (!departmentIds.some((id) => Number(id) === Number(state.eventDepartmentFilter))) return false;
  }

  if (state.eventManagerFilter !== "all") {
    const managerIds = event.manager_ids || [event.manager_id];
    if (!managerIds.some((id) => Number(id) === Number(state.eventManagerFilter))) return false;
  }

  if (state.eventStatusFilter !== "all" && event.status !== state.eventStatusFilter) {
    return false;
  }

  if (state.eventCustomerFilter && state.eventCustomerFilter !== "all") {
    if (String(event.client_name || "") !== String(state.eventCustomerFilter)) return false;
  }

  return true;
}


function renderAdminEvents(data, mode = "active") {
  const groupedEvents = groupedAdminEventsForTable(data.events || []);
  const byMode = mode === "archive"
    ? groupedEvents.filter((event) => eventIsMoneyArchive(event))
    : groupedEvents.filter((event) => !eventIsMoneyArchive(event));
  const events = byMode.filter(eventMatchesAdminFilters);
  return `
    ${renderEventFilters(byMode)}
    ${renderEventsTable(events, true)}
  `;
}

function planEditorYear() {
  const year = Number(String(state.month || "").slice(0, 4));
  return Number.isFinite(year) && year > 2000 ? year : new Date().getFullYear();
}

function monthlyPlanKey(year, monthValue) {
  return `${year}-${monthValue}`;
}

function planMonthDate(year, monthValue) {
  return `${year}-${monthValue}-01`;
}

function monthlyPlansByMonth(year) {
  const map = new Map();
  (state.monthlyPlans || []).forEach((plan) => {
    const monthKey = String(plan.month || "").slice(0, 7);
    if (monthKey.startsWith(`${year}-`)) map.set(monthKey, plan);
  });
  return map;
}

function planPercentValue(plan, key, fallback) {
  const value = plan?.[key] ?? fallback;
  const number = normalizeNumberInput(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatPercentValue(value) {
  const number = Math.round(normalizeNumberInput(value) * 100) / 100;
  return String(number).replace(/\.00$/, "").replace(/(\.\d)0$/, "$1");
}

function renderPlanPercentInput(monthValue, kind, value, label) {
  const shortLabel = label === "Менеджер" ? "Мен." : label;
  return `
    <label class="plan-percent-cell plan-percent-cell-${kind}">
      <span>${shortLabel}</span>
      <span class="plan-percent-control">
        <input class="plan-percent-input" data-plan-percent="${kind}" data-plan-month="${monthValue}" inputmode="decimal" value="${formatPercentValue(value)}" />
        <b>%</b>
      </span>
    </label>
  `;
}

function renderPlansSkeleton(data) {
  const year = planEditorYear();
  const isLoaded = Number(state.monthlyPlansYear) === Number(year);
  const plans = monthlyPlansByMonth(year);

  return `
    <section class="plans-editor" id="plansEditor" data-plans-year="${year}">
      <div class="block-title plans-editor-title">
        <div>
          <h3>Задать планы на ${year}</h3>
          <p class="muted">Каждый месяц хранит свой план и свои проценты. Прошлые месяцы не переписываются.</p>
        </div>
        <button id="savePlansYearBtn" class="secondary" ${isLoaded ? "" : "disabled"}>Сохранить планы</button>
      </div>

      ${!isLoaded ? `<div class="empty-state">Загружаем планы за ${year}…</div>` : `
        <div class="plans-help-card plans-help-card-compact">
          <strong>Проценты отдельно по месяцам.</strong>
          <span>Санжар и Рауфаль в каждой строке автоматически дают 100%.</span>
        </div>

        <div class="plans-table-wrap">
          <table class="plans-table plans-table-monthly">
            <thead>
              <tr>
                <th>Месяц</th>
                <th>Компания</th>
                <th>Отделы %</th>
                <th>Санжар</th>
                <th>Рауфаль</th>
                <th>Мен. %</th>
                <th>Менеджер</th>
              </tr>
            </thead>
            <tbody>
              ${MONTHS_RU.map(([monthValue, label]) => {
                const key = monthlyPlanKey(year, monthValue);
                const plan = plans.get(key);
                const companyPlan = plan?.company_plan_amount ?? "";
                const sanzharPercent = planPercentValue(plan, "sanzhar_share_percent", 66.67);
                const raufalPercent = planPercentValue(plan, "raufal_share_percent", 33.33);
                const managerPercent = planPercentValue(plan, "manager_personal_plan_percent", 12.5);
                return `
                  <tr data-plan-row="${monthValue}">
                    <td><strong>${label}</strong></td>
                    <td>
                      <input class="plan-month-input" data-month-plan-input="${monthValue}" inputmode="numeric" value="${formatInputNumber(companyPlan)}" placeholder="0" />
                    </td>
                    <td>
                      <div class="plan-percent-pair">
                        ${renderPlanPercentInput(monthValue, "sanzhar", sanzharPercent, "Санжар")}
                        ${renderPlanPercentInput(monthValue, "raufal", raufalPercent, "Рауфаль")}
                      </div>
                    </td>
                    <td data-plan-calc-sanzhar="${monthValue}">0</td>
                    <td data-plan-calc-raufal="${monthValue}">0</td>
                    <td>
                      ${renderPlanPercentInput(monthValue, "manager", managerPercent, "Менеджер")}
                    </td>
                    <td data-plan-calc-manager="${monthValue}">0</td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>

        <div id="plansSaveMessage" class="muted plans-save-message"></div>
      `}
    </section>
  `;
}


function monthLabelRu(monthKey) {
  const value = String(monthKey || state.month || "").slice(5, 7);
  const month = MONTHS_RU.find(([key]) => key === value);
  const year = String(monthKey || state.month || "").slice(0, 4);
  return `${month?.[1] || value} ${year}`.trim();
}

function closingStatusLabel(status) {
  if (status === "closed") return "Закрыт";
  if (status === "reopened") return "Открыт заново";
  return "Не закрыт";
}

function closingMonthDate(monthKey = state.month) {
  return `${String(monthKey || "").slice(0, 7)}-01`;
}

function departmentDefaultSplitLabel() {
  const depSanzhar = (state.adminData?.departments || []).find((dep) => String(dep.department_name || "").includes("Санжар"));
  const companyPlan = asNumber(state.adminData?.company_plan_amount);
  const sanzharPlan = asNumber(depSanzhar?.plan_amount);
  const sanzharPercent = companyPlan > 0 ? Math.round((sanzharPlan / companyPlan) * 10000) / 100 : 66.67;
  const raufalPercent = Math.round((100 - sanzharPercent) * 100) / 100;
  return `${formatPercentValue(sanzharPercent)} / ${formatPercentValue(raufalPercent)}%`;
}

function expenseAllocationLabel(expense) {
  const type = expense?.allocation_type;
  if (type === "sanzhar_only") return "Санжар";
  if (type === "raufal_only") return "Рауфаль";
  if (type === "custom") return "Вручную";
  return `По плану ${departmentDefaultSplitLabel()}`;
}

function renderClosingSkeleton(data) {
  return `
    <section class="closing-panel" id="closingPanel" data-closing-month="${state.month}">
      <div class="block-title closing-title">
        <div>
          <h3>Закрыть месяц</h3>
          <p class="muted">Расходы за ${monthLabelRu(state.month)}. Калькуляция подтянется после загрузки расходов.</p>
        </div>
      </div>
      <div class="empty-state">Загружаем расходы месяца…</div>
    </section>
  `;
}

function renderClosingExpenseRows(expenses) {
  if (!expenses.length) {
    return `<div class="empty-state closing-empty">Расходов за месяц пока нет.</div>`;
  }

  return `
    <div class="closing-table-wrap">
      <table class="closing-table closing-expenses-table">
        <thead>
          <tr>
            <th>Расход</th>
            <th>Сумма</th>
            <th>Деление</th>
            <th>Санжар</th>
            <th>Рауфаль</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${expenses.map((expense) => {
            const isEditing = Number(state.closingEditingExpenseId) === Number(expense.id);
            return `
              <tr class="${isEditing ? "is-editing" : ""}">
                <td>
                  <strong>${escapeHtml(expense.title || "Расход")}</strong>
                  ${expense.comment ? `<small>${escapeHtml(expense.comment)}</small>` : ""}
                </td>
                <td>
                  ${isEditing ? `
                    <input
                      class="closing-edit-amount-input"
                      data-edit-expense-amount-id="${expense.id}"
                      inputmode="numeric"
                      value="${escapeHtml(integerInputValue(expense.amount))}"
                      aria-label="Новая сумма расхода"
                    />
                  ` : formatMoney(expense.amount)}
                </td>
                <td>${expenseAllocationLabel(expense)}</td>
                <td>${formatMoney(expense.sanzhar_amount)}</td>
                <td>${formatMoney(expense.raufal_amount)}</td>
                <td>
                  <div class="closing-row-actions">
                    ${isEditing ? `
                      <button class="closing-icon-btn success" data-save-expense-id="${expense.id}" type="button" title="Сохранить сумму">✓</button>
                      <button class="closing-icon-btn neutral" data-cancel-edit-expense-id="${expense.id}" type="button" title="Отменить редактирование">↺</button>
                    ` : `
                      <button class="closing-icon-btn edit" data-edit-expense-id="${expense.id}" type="button" title="Изменить сумму">✎</button>
                      <button class="closing-icon-btn danger" data-delete-expense-id="${expense.id}" type="button" title="Удалить расход">×</button>
                    `}
                  </div>
                </td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function closingDepartmentCard(title, prefix, calc) {
  return `
    <article class="closing-department-card ${departmentClassByName(title)}">
      <div class="closing-card-head">
        <h4>${title}</h4>
        <span>${formatPercentValue(calc?.[`${prefix}_completion_percent`] || 0)}%</span>
      </div>
      <div class="closing-lines">
        <div><span>План</span><b>${formatMoney(calc?.[`${prefix}_plan_amount`] || 0)}</b></div>
        <div><span>Факт</span><b>${formatMoney(calc?.[`${prefix}_income_amount`] || 0)}</b></div>
        <div><span>Расходы</span><b>${formatMoney(calc?.[`${prefix}_expense_amount`] || 0)}</b></div>
        <div><span>Руководитель</span><b>${formatMoney(calc?.[`${prefix}_head_salary`] || 0)} · ${formatPercentValue(calc?.[`${prefix}_head_percent`] || 0)}%</b></div>
        <div class="total"><span>Остаток</span><b>${formatMoney(calc?.[`${prefix}_remaining_after_head`] || 0)}</b></div>
      </div>
    </article>
  `;
}

function renderClosingCalculation(calc, closing, calcPending = false) {
  if (!calc) {
    if (calcPending) {
      return `<div class="empty-state closing-empty">Расходы уже загружены. Калькуляция подтягивается в фоне…</div>`;
    }
    return `<div class="empty-state closing-empty">Сначала задайте план месяца во вкладке «Задать планы».</div>`;
  }

  return `
    <div class="closing-calc-grid">
      ${closingDepartmentCard("Санжар", "sanzhar", calc)}
      ${closingDepartmentCard("Рауфаль", "raufal", calc)}
    </div>

    <div class="closing-founders-card">
      <div class="closing-card-head">
        <h4>Учредители</h4>
        <span>${formatMoney(calc.founders_total_amount || 0)}</span>
      </div>
      <div class="closing-founders-grid">
        <div><span>Александр</span><b>${formatMoney(calc.founder_one_amount || 0)}</b></div>
        <div><span>Дмитрий</span><b>${formatMoney(calc.founder_two_amount || 0)}</b></div>
        <div><span>Иван</span><b>${formatMoney(calc.founder_three_amount || 0)}</b></div>
      </div>
    </div>
  `;
}

function renderClosingContent(expenses, calc, closing, error = null, calcPending = false) {
  const status = closing?.status || state.adminData?.closing?.status || "draft";
  const isClosed = status === "closed";

  return `
    <div class="block-title closing-title">
      <div>
        <h3>Закрыть месяц</h3>
        <p class="muted">${monthLabelRu(state.month)} · вкладка только хранит расходы и расчёт; месяц закрывается только кнопкой ниже.</p>
      </div>
      <div class="closing-status-row">
        ${calcPending ? `<span class="closing-status pending">Считаем…</span>` : ""}
        <span class="closing-status ${isClosed ? "closed" : "draft"}">${closingStatusLabel(status)}</span>
      </div>
    </div>

    ${error ? `<div class="error closing-error">${escapeHtml(error)}</div>` : ""}

    <section class="closing-mini-section">
      <div class="closing-section-head">
        <h4>Расходы</h4>
        <span>${formatMoney((expenses || []).reduce((sum, item) => sum + asNumber(item.amount), 0))} · ${departmentDefaultSplitLabel()}</span>
      </div>
      <div class="closing-expense-form">
        <input id="closingExpenseTitle" placeholder="Название" />
        <input id="closingExpenseAmount" inputmode="numeric" placeholder="Сумма" />
        <select id="closingExpenseAllocation">
          <option value="default_split">По плану месяца</option>
          <option value="sanzhar_only">100% Санжар</option>
          <option value="raufal_only">100% Рауфаль</option>
          <option value="custom">Вручную</option>
        </select>
        <input id="closingExpenseSanzhar" class="closing-custom-split hidden" inputmode="numeric" placeholder="Санжар" />
        <input id="closingExpenseRaufal" class="closing-custom-split hidden" inputmode="numeric" placeholder="Рауфаль" />
        <input id="closingExpenseComment" placeholder="Комментарий" />
        <button id="addClosingExpenseBtn" type="button">Добавить</button>
      </div>
      ${renderClosingExpenseRows(expenses || [])}
    </section>

    <section class="closing-mini-section">
      <div class="closing-section-head">
        <h4>Калькуляция</h4>
        <span>${calcPending ? "обновляется в фоне…" : "10% / 15%"}</span>
      </div>
      ${renderClosingCalculation(calc, closing, calcPending)}
      ${calcPending ? `<div class="muted closing-message">Расход сохранён. Калькуляция обновится автоматически через пару секунд.</div>` : ""}
      <div class="closing-actions">
        <button id="recalculateClosingBtn" class="secondary" type="button">Пересчитать</button>
        ${isClosed ? `
          <button id="reopenClosingBtn" class="secondary" type="button">Открыть месяц</button>
        ` : `
          <button id="closeMonthBtn" type="button">Закрыть месяц</button>
        `}
      </div>
      <div id="closingMessage" class="muted closing-message"></div>
    </section>
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
  attachManagerDeleteButtons();
  attachPlansModal();
  attachClosingPanel();
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
    $("dashboardContent").innerHTML = renderAdminEvents(data, "active");
  } else if (state.activeAdminTab === "events_archive") {
    $("dashboardContent").innerHTML = renderAdminEvents(data, "archive");
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
  attachManagerDeleteButtons();
  attachPlansModal();
  attachClosingPanel();
}

function renderDepartmentDashboard(data, paymentRequests = []) {
  data = data || {};
  state.departmentHeadData = data;
  renderDepartmentHeadTabs();
  renderSummary([]);

  $("dashboardTitle").textContent = `Кабинет отдела: ${data.department_name || ""}`;
  $("dashboardHint").textContent = "";

  if (state.activeDepartmentHeadTab === "events") {
    $("dashboardContent").innerHTML = renderDepartmentHeadEventsTable(data.events || []);
  } else if (state.activeDepartmentHeadTab === "requests") {
    if (state.paymentStatusFilter === "active") state.paymentStatusFilter = "all";
    $("dashboardContent").innerHTML = renderDepartmentHeadRequestsTable(data.payment_requests || paymentRequests || []);
  } else if (state.activeDepartmentHeadTab === "totals") {
    $("dashboardContent").innerHTML = renderDepartmentHeadTotals(data);
  } else {
    $("dashboardContent").innerHTML = renderDepartmentHeadOverview(data);
  }

  attachEventRows();
  attachDepartmentHeadFilters();
  attachDepartmentHeadExpensesModal();
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
              <em data-mini-status class="status-badge ${eventStatusToneClass(event.status)}">${statusLabel(event.status)}</em>${eventMoneyStatus(event) === "cash_received" ? `<em class="status-badge status-tone-accepted">Деньги в кассе</em>` : ""}
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

  if (field === "external_amount_admin") {
    const amount = value === "" ? 0 : Math.round(normalizeNumberInput(value));
    item.external_price = amount;
    item.external_quantity = 1;
    item.external_days = 1;
  } else if (["external_price", "external_quantity", "external_days", "amount_fact"].includes(field)) {
    item[field] = value === "" ? null : Math.round(normalizeNumberInput(value));
  } else {
    item[field] = value;
  }

  if (field === "payment_method") {
    if (value !== "self_employed") {
      clearDraftSelfEmployedFields(item);
    }

    if (value !== "invoice") {
      item.iin_bin = null;
      item.iin_bin_locked = false;
      item.tax_check_status = null;
    }

    if (value === "cash" || value === "card" || value === "" || value === "invoice") {
      item.vat_amount = 0;
      item.deduction_amount = 0;
    }

    if (value === "self_employed") {
      ensureSelfEmployedItemTax(item);
    }
  }

  if (["external_price", "external_quantity", "external_days", "external_amount_admin"].includes(field) && item.item_type === "coordinator") {
    item.amount_fact = Math.round(externalRowAmount(item) * 0.5);
  }

  if (field === "amount_fact" && (item.payment_method === "self_employed" || item.tax_check_status === "self_employed")) {
    ensureSelfEmployedItemTax(item);
  }

  if (["amount_fact", "external_price", "external_quantity", "external_days", "external_amount_admin"].includes(field)) {
    recalculateCheckedItemTax(item);
  }
  updateCurrentManagerMiniCardLive();
}


function attachDraftEventInputs(eventId) {
  document.querySelectorAll("[data-event-field]").forEach((input) => {
    input.disabled = input.disabled || !canEditManagerEvent(state.currentManagerEvent);

    input.addEventListener("input", () => {
      if (input.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
      setDraftEventValue(eventId, input.getAttribute("data-event-field"), input.value);
      refreshDraftVisibleCalculations(eventId);
      updateCurrentManagerMiniCardLive();
    });

    input.addEventListener("change", () => {
      if (input.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
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
    input.disabled = input.disabled || !canEditManagerEvent(state.currentManagerEvent);

    input.addEventListener("input", () => {
      if (input.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
      const itemId = input.getAttribute("data-item-id");
      const field = input.getAttribute("data-item-field");
      setDraftItemValue(eventId, itemId, field, input.value);
      refreshDraftVisibleCalculations(eventId);
      updateTaxUiInPlace(itemId);
    });

    input.addEventListener("change", () => {
      if (input.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
      const itemId = input.getAttribute("data-item-id");
      const field = input.getAttribute("data-item-field");
      setDraftItemValue(eventId, itemId, field, input.value);

      if (["external_price", "external_amount_admin", "amount_fact"].includes(field)) {
        const items = getDraftItems(eventId);
        const item = items.find((candidate) => String(candidate.id) === String(itemId));
        input.value = field === "amount_fact" ? internalFactDisplayValue(item) : formatInputNumber(field === "external_amount_admin" ? externalRowAmount(item) : item?.external_price);
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

  const activeTab = isAdminEditMode ? "internal" : (state.managerEstimateTab || "external");
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
  if (["accepted", "approved", "completed", "done", "archive", "archived", "cash_received"].includes(normalized)) return "status-tone-accepted";
  if (["revision", "needs_revision", "rework"].includes(normalized)) return "status-tone-draft";
  return "status-tone-draft";
}

function canEditManagerEvent(event) {
  const user = state.bootstrap?.user;
  if (user?.role === "admin" && Number(state.adminEventEditModeId || 0) === Number(event?.id || 0)) {
    return event?.status !== "cancelled";
  }
  return ["draft", "revision"].includes(String(event?.status || ""));
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
  if (item.item_type === "coordinator") return `<span class="drag-handle muted" title="Координатор всегда первый">↕</span>`;
  return `<span class="drag-handle" draggable="true" data-drag-item="${item.id}" title="Перетащить строку">↕</span>`;
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
        <colgroup>
          <col class="drag-col" />
          <col class="position-col" />
          <col class="plan-col" />
          <col class="fact-col" />
          <col class="commission-col" />
          <col class="payment-col" />
          <col class="bin-col" />
          <col class="kgd-col" />
          <col class="vat-col" />
          <col class="deduction-col" />
          <col class="paid-col" />
          <col class="actions-col" />
        </colgroup>
        <thead>
          <tr>
            <th class="drag-col"></th>
            <th>Позиция</th>
            <th>Смета</th>
            <th>Факт</th>
            <th class="commission-col">Комиссия</th>
            <th>Оплата</th>
            <th>БИН/ИИН</th>
            <th class="kgd-col">КГД</th>
            <th class="vat-col">НДС</th>
            <th class="deduction-col">Вычеты</th>
            <th class="paid-col">Оплачено</th>
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
                <td>${state.bootstrap?.user?.role === "admin" && Number(state.adminEventEditModeId || 0) === Number(event?.id || 0)
                  ? rowInput(formatInputNumber(externalRowAmount(item)), `data-item-field="external_amount_admin" data-item-id="${item.id}"`)
                  : `<strong>${formatMoney(externalRowAmount(item))}</strong>`}</td>
                <td>${rowInput(internalFactDisplayValue(item), `data-item-field="amount_fact" data-item-id="${item.id}" ${item.item_type === "coordinator" ? "disabled" : ""}`)}</td>
                <td class="commission-col"><strong>${formatMoney(internalCommissionValue(item))}</strong></td>
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
                <td class="kgd-col">
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
  const isAdminEditMode = state.bootstrap?.user?.role === "admin" && Number(state.adminEventEditModeId || 0) === Number(event?.id || 0);
  const canEdit = canEditManagerEvent(event);
  const canDelete = canDeleteManagerEvent(event);
  const eventDeleteLocked = eventHasActivePaymentRequests(event);
  const eventDeleteAllowed = canDelete && !eventDeleteLocked;
  const eventDeleteTitle = eventDeleteDisabledReason(event);
  const isReadonlyReview = !isAdminEditMode && event?.status === "review";
  const readonlyAttrs = canEdit ? "" : "disabled";


  const activeTab = isAdminEditMode ? "internal" : (state.managerEstimateTab || "external");

  return `
    <section class="manager-event-card ${isReadonlyReview ? "is-readonly" : ""}" style="${isReadonlyReview ? "background: rgba(115,120,130,.045);" : ""}">
      <div class="manager-event-head">
        <div>
          <div class="overview-label">${isAdminEditMode ? "Редактирование админом" : "Карточка мероприятия"}</div>
          <h2>${event.title}</h2>
          <div class="event-badge-row">
            <span class="status ${event.status} ${eventStatusToneClass(event.status)}">${statusLabel(event.status)}</span>${eventMoneyStatus(event) === "cash_received" ? `<span class="status cash_received status-tone-accepted">Деньги в кассе</span>` : ""}
            ${coauthorBadgeHtml(event)}
          </div>
        </div>
        <div class="inline-actions">
          ${isAdminEditMode ? `
            <span class="status-badge status-tone-review">✏️ Админ-редактирование</span>
          ` : `
            <button class="secondary" data-manager-event-pay="${event.id}">Оплатить</button>
            <button class="ghost" data-manager-event-payments="${event.id}">Мои оплаты</button>
            <button class="ghost" data-manager-event-transfer="${event.id}">Передать</button>
            ${eventIsCoauthored(event)
              ? `<button class="ghost" data-manager-event-remove-coauthor="${event.id}">Удалить соавтора</button>`
              : `<button class="ghost" data-manager-event-coauthor="${event.id}">Соавтор</button>`}
            <button class="danger-btn" data-manager-event-delete="${event.id}" title="${eventDeleteTitle}" ${eventDeleteAllowed ? "" : "disabled"} style="margin-left:auto;" ${eventMoneyStatus(event) === "cash_received" ? 'disabled title="Нельзя удалить: деньги уже в кассе"' : ""}>Удалить</button>
          `}
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

      ${isAdminEditMode ? "" : `
        <div class="estimate-tabs">
          <button class="${activeTab === "external" ? "tab-btn active" : "ghost"}" data-estimate-tab="external">Внешняя смета</button>
          <button class="${activeTab === "internal" ? "tab-btn active" : "ghost"}" data-estimate-tab="internal">Внутренняя смета</button>
        </div>
      `}

      <div id="managerEstimatePanel">
        ${isAdminEditMode ? renderInternalEstimate(items || [], event, summary) : (activeTab === "external" ? renderExternalEstimate(items || [], event.id, event) : renderInternalEstimate(items || [], event, summary))}
      </div>

      ${summary && (activeTab === "internal" || isAdminEditMode) ? `
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
        ${isAdminEditMode ? `
          <button class="save-draft-btn" data-admin-event-save-edit="${event.id}">Сохранить изменения</button>
          <button class="ghost" data-admin-event-cancel-edit="${event.id}">Отмена</button>
        ` : `
          <button class="save-draft-btn ${canEdit ? "" : "disabled-action"}" data-manager-event-save-draft="${event.id}" ${readonlyAttrs}>Сохранить черновик</button>
          <button class="${canEdit ? "" : "disabled-action"}" data-manager-event-send-review="${event.id}" ${readonlyAttrs}>Отправить Саше</button>
        `}
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
  const stalePaymentsModal = $("plansModalBackdrop") || $("eventModalBackdrop");
  if (stalePaymentsModal) stalePaymentsModal.classList.remove("manager-payments-modal");
  // openManagerCreateModal_removeManagerPaymentsModal_v03712

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
      clearDraftSelfEmployedFields(item);
      item.deduction_amount = 0;
    }
  } else {
    clearDraftSelfEmployedFields(item);
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
  const isAdminEditMode = state.bootstrap?.user?.role === "admin" && Number(state.adminEventEditModeId || 0) === Number(state.selectedManagerEventId || 0);
  const holder = isAdminEditMode ? $("eventModalContent") : $("managerEventDetail");
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

  // Самозанятый становится жёстко закреплённым только после активной заявки/оплаты
  // по этой позиции. Простое переключение в смете остаётся обычным черновым выбором.
  const isSelfEmployed = item.payment_method === "self_employed" || itemHasActiveSelfEmployedPaymentRequest(item);
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

function clearDraftSelfEmployedFields(item) {
  if (!item || itemHasActiveSelfEmployedPaymentRequest(item)) return item;

  if (item.tax_check_status === "self_employed") {
    item.tax_check_status = null;
  }

  if (String(item.internal_note || "").match(/^Самозанятый:\s*/i)) {
    item.internal_note = null;
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
  return itemHasActiveSelfEmployedPaymentRequest(item);
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
  if (itemHasActiveSelfEmployedPaymentRequest(item)) return "self_employed";
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
  // Заявка на оплату не должна пытаться сохранить само мероприятие.
  // На статусах «На проверке»/«Принято» редактирование мероприятия закрыто,
  // но создание оплаты/допрасхода по факту разрешено.
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
  resetEventModalModes();
  // openManagerPaymentModal_resetSharedChrome_v03715

  const backdrop = $("eventModalBackdrop");
  const title = $("eventModalTitle");
  const content = $("eventModalContent");
  if (!backdrop || !title || !content) return;

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
  const isAdminEditMode = state.bootstrap?.user?.role === "admin" && Number(state.adminEventEditModeId || 0) === Number(state.currentManagerEvent?.id || 0);

  document.querySelectorAll("[data-admin-event-save-edit]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-admin-event-save-edit");
      if (!eventId || button.disabled) return;

      try {
        await withLoading(async () => {
          await saveDraftEvent(eventId);
          await saveDraftItems(eventId);
          showToast("Изменения сохранены");
          await closeAdminEventEditMode(eventId, false);
          await openEventModal(eventId);
          await loadDashboard();
        }, "Сохраняем изменения…");
      } catch (error) {
        alert(error.message || "Не удалось сохранить изменения");
      }
    });
  });

  document.querySelectorAll("[data-admin-event-cancel-edit]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-admin-event-cancel-edit");
      await closeAdminEventEditMode(eventId, true);
    });
  });

  document.querySelectorAll("[data-estimate-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.managerEstimateTab = button.getAttribute("data-estimate-tab");
      if (isAdminEditMode) {
        const content = $("eventModalContent");
        if (content) {
          const items = getDraftItems(state.selectedManagerEventId);
          const summary = calculateDraftSummaryPreview(items, state.currentManagerEvent, state.currentManagerSummary);
          state.currentManagerSummary = summary;
          state.currentManagerItems = items;
          content.innerHTML = renderManagerEventCard(state.currentManagerEvent, items, summary);
          attachManagerCreateWorkspaceActions();
          attachDraftEventInputs(state.selectedManagerEventId);
          attachDraftInputs(state.selectedManagerEventId);
        }
      } else {
        renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
      }
    });
  });

  const addExternalBtn = document.getElementById("addExternalPositionBtn");
  const addInternalBtn = document.getElementById("addInternalPositionBtn");
  [addExternalBtn, addInternalBtn].filter(Boolean).forEach((button) => {
    button.disabled = !managerCardCanEdit;
    button.classList.toggle("disabled-action", !managerCardCanEdit);
    button.addEventListener("click", () => {
      if (!canEditManagerEvent(state.currentManagerEvent)) return;
      addDraftRegularPosition(state.selectedManagerEventId);
      if (isAdminEditMode) {
        rerenderCurrentManagerCard();
      } else {
        renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
      }
    });
  });

  document.querySelectorAll("[data-delete-item]").forEach((button) => {
    button.disabled = button.disabled || !managerCardCanEdit;
    button.classList.toggle("disabled-action", !managerCardCanEdit);
    button.addEventListener("click", () => {
      if (button.disabled) return;
      if (!canEditManagerEvent(state.currentManagerEvent)) return;
      if (!confirm("Удалить позицию?")) return;
      deleteDraftItem(state.selectedManagerEventId, button.getAttribute("data-delete-item"));
      if (isAdminEditMode) {
        rerenderCurrentManagerCard();
      } else {
        renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
      }
    });
  });

  document.querySelectorAll("[data-manager-event-save-draft]").forEach((button) => {
    button.disabled = !managerCardCanEdit;
    button.classList.toggle("disabled-action", !managerCardCanEdit);
    button.addEventListener("click", async () => {
      if (button.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
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
    button.disabled = !managerCardCanEdit;
    button.classList.toggle("disabled-action", !managerCardCanEdit);
    button.addEventListener("click", async () => {
      if (button.disabled || !canEditManagerEvent(state.currentManagerEvent)) return;
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
      if (!canEditManagerEvent(state.currentManagerEvent)) return;

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
  resetEventModalModes();
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

async function loadClosingByMonth(month) {
  try {
    return await api(`/monthly-closings/by-month?month=${month}&_=${Date.now()}`);
  } catch (error) {
    const message = String(error.message || "");
    if (message.includes("404") || message.includes("Monthly closing not found")) return null;
    throw error;
  }
}

async function loadClosingPanelData(options = {}) {
  const month = state.month;
  const includeCalculation = Boolean(options.includeCalculation);
  const cached = state.closingPanelData && state.closingPanelData.month === month
    ? state.closingPanelData
    : null;

  if (!includeCalculation) {
    const [expenses, closing] = await Promise.allSettled([
      api(`/monthly-expenses?month=${month}&_=${Date.now()}`),
      loadClosingByMonth(month),
    ]);

    return {
      month,
      expenses: expenses.status === "fulfilled" && Array.isArray(expenses.value) ? expenses.value : [],
      calc: cached?.calc || null,
      closing: closing.status === "fulfilled" ? closing.value : cached?.closing || null,
      error: expenses.status === "rejected" ? expenses.reason?.message : null,
      calcPending: true,
    };
  }

  const [expenses, calcResult, closing] = await Promise.allSettled([
    api(`/monthly-expenses?month=${month}&_=${Date.now()}`),
    api(`/monthly-closings/calculate?month=${month}&_=${Date.now()}`),
    loadClosingByMonth(month),
  ]);

  if (calcResult.status === "rejected") {
    return {
      month,
      expenses: expenses.status === "fulfilled" && Array.isArray(expenses.value) ? expenses.value : cached?.expenses || [],
      calc: cached?.calc || null,
      closing: closing.status === "fulfilled" ? closing.value : cached?.closing || null,
      error: calcResult.reason?.message || "Не удалось рассчитать закрытие месяца",
      calcPending: false,
    };
  }

  return {
    month,
    expenses: expenses.status === "fulfilled" && Array.isArray(expenses.value) ? expenses.value : cached?.expenses || [],
    calc: calcResult.value,
    closing: closing.status === "fulfilled" ? closing.value : cached?.closing || null,
    error: expenses.status === "rejected" ? expenses.reason?.message : null,
    calcPending: false,
  };
}

function setClosingCustomSplitVisibility() {
  const allocation = document.getElementById("closingExpenseAllocation")?.value;
  document.querySelectorAll(".closing-custom-split").forEach((input) => {
    input.classList.toggle("hidden", allocation !== "custom");
  });
}

function captureClosingExpenseDraft() {
  const panel = document.getElementById("closingPanel");
  if (!panel || panel.dataset.closingMonth !== String(state.month)) return null;

  const fieldIds = [
    "closingExpenseTitle",
    "closingExpenseAmount",
    "closingExpenseAllocation",
    "closingExpenseSanzhar",
    "closingExpenseRaufal",
    "closingExpenseComment",
  ];
  const fields = {};
  fieldIds.forEach((id) => {
    const input = document.getElementById(id);
    if (input) fields[id] = input.value;
  });

  const active = document.activeElement;
  const activeId = active?.id || null;
  const activeEditExpenseId = active?.dataset?.editExpenseAmountId || null;
  const editInput = document.querySelector("[data-edit-expense-amount-id]");

  return {
    month: state.month,
    fields,
    activeId,
    activeEditExpenseId,
    editExpenseId: editInput?.dataset?.editExpenseAmountId || null,
    editExpenseAmount: editInput?.value || null,
    selectionStart: typeof active?.selectionStart === "number" ? active.selectionStart : null,
    selectionEnd: typeof active?.selectionEnd === "number" ? active.selectionEnd : null,
  };
}

function restoreClosingExpenseDraft(draft) {
  if (!draft || draft.month !== state.month) return;

  Object.entries(draft.fields || {}).forEach(([id, value]) => {
    const input = document.getElementById(id);
    if (input) input.value = value;
  });
  setClosingCustomSplitVisibility();

  if (draft.editExpenseId && draft.editExpenseAmount !== null) {
    const editInput = document.querySelector(`[data-edit-expense-amount-id="${draft.editExpenseId}"]`);
    if (editInput) editInput.value = draft.editExpenseAmount;
  }

  const focusTarget = draft.activeEditExpenseId
    ? document.querySelector(`[data-edit-expense-amount-id="${draft.activeEditExpenseId}"]`)
    : (draft.activeId ? document.getElementById(draft.activeId) : null);

  if (focusTarget && typeof focusTarget.focus === "function") {
    focusTarget.focus();
    if (typeof focusTarget.setSelectionRange === "function" && draft.selectionStart !== null && draft.selectionEnd !== null) {
      try {
        focusTarget.setSelectionRange(draft.selectionStart, draft.selectionEnd);
      } catch (_) {
        // Some input types do not support selection ranges.
      }
    }
  }
}

function renderClosingPanelFromCache() {
  const panel = document.getElementById("closingPanel");
  const data = state.closingPanelData;
  if (!panel || !data || data.month !== state.month) return;

  const draft = captureClosingExpenseDraft();

  panel.dataset.eventsAttached = "0";
  panel.innerHTML = renderClosingContent(
    data.expenses || [],
    data.calc || null,
    data.closing || null,
    data.error || null,
    Boolean(data.calcPending),
  );
  attachClosingPanelEvents();
  restoreClosingExpenseDraft(draft);
}

function cacheClosingPanelData(data) {
  state.closingPanelData = {
    month: data?.month || state.month,
    expenses: Array.isArray(data?.expenses) ? data.expenses : [],
    calc: data?.calc || null,
    closing: data?.closing || null,
    error: data?.error || null,
    calcPending: Boolean(data?.calcPending),
  };
}

function scheduleClosingCalculationRefresh(delayMs = 900) {
  clearTimeout(state.closingCalcRefreshTimer);

  state.closingCalcRefreshTimer = setTimeout(async () => {
    const month = state.month;
    const requestSeq = state.closingCalcRefreshSeq + 1;
    state.closingCalcRefreshSeq = requestSeq;

    try {
      const [calcResult, closing] = await Promise.allSettled([
        api(`/monthly-closings/calculate?month=${month}&_=${Date.now()}`),
        loadClosingByMonth(month),
      ]);

      if (requestSeq !== state.closingCalcRefreshSeq || state.month !== month) return;

      const current = state.closingPanelData && state.closingPanelData.month === month
        ? state.closingPanelData
        : { month, expenses: [] };

      state.closingPanelData = {
        ...current,
        calc: calcResult.status === "fulfilled" ? calcResult.value : current.calc || null,
        closing: closing.status === "fulfilled" ? closing.value : current.closing || null,
        error: calcResult.status === "rejected" ? (calcResult.reason?.message || "Не удалось пересчитать месяц") : null,
        calcPending: false,
      };
      renderClosingPanelFromCache();
    } catch (error) {
      const current = state.closingPanelData && state.closingPanelData.month === month
        ? state.closingPanelData
        : { month, expenses: [] };
      state.closingPanelData = { ...current, error: error.message, calcPending: false };
      renderClosingPanelFromCache();
    }
  }, delayMs);
}

function markClosingCalculationPending() {
  const current = state.closingPanelData && state.closingPanelData.month === state.month
    ? state.closingPanelData
    : { month: state.month, expenses: [], calc: null, closing: null, error: null };

  state.closingPanelData = { ...current, calcPending: true, error: null };
  renderClosingPanelFromCache();
  scheduleClosingCalculationRefresh();
}

async function refreshClosingPanel(options = {}) {
  const panel = document.getElementById("closingPanel");
  if (!panel) return;

  const loadedForMonth = panel.dataset.closingMonth;
  if (loadedForMonth !== String(state.month)) return;

  const includeCalculation = Boolean(options.includeCalculation);

  try {
    const data = await loadClosingPanelData({ includeCalculation });
    cacheClosingPanelData(data);
    renderClosingPanelFromCache();
    if (!includeCalculation && !data.error) {
      scheduleClosingCalculationRefresh(250);
    }
  } catch (error) {
    cacheClosingPanelData({ month: state.month, expenses: [], calc: null, closing: null, error: error.message, calcPending: false });
    renderClosingPanelFromCache();
  }
}

function clearClosingExpenseForm() {
  ["closingExpenseTitle", "closingExpenseAmount", "closingExpenseComment", "closingExpenseSanzhar", "closingExpenseRaufal"].forEach((id) => {
    const input = document.getElementById(id);
    if (input) input.value = "";
  });
  const allocationInput = document.getElementById("closingExpenseAllocation");
  if (allocationInput) allocationInput.value = "default_split";
  setClosingCustomSplitVisibility();
}

function insertClosingExpenseIntoCache(expense) {
  if (!expense) return false;
  const current = state.closingPanelData && state.closingPanelData.month === state.month
    ? state.closingPanelData
    : null;
  if (!current) return false;

  const existing = Array.isArray(current.expenses) ? current.expenses : [];
  state.closingPanelData = {
    ...current,
    expenses: [expense, ...existing.filter((item) => Number(item.id) !== Number(expense.id))],
    calcPending: true,
    error: null,
  };
  renderClosingPanelFromCache();
  scheduleClosingCalculationRefresh();
  return true;
}

function removeClosingExpenseFromCache(expenseId) {
  const current = state.closingPanelData && state.closingPanelData.month === state.month
    ? state.closingPanelData
    : null;
  if (!current) return false;

  state.closingPanelData = {
    ...current,
    expenses: (current.expenses || []).filter((item) => Number(item.id) !== Number(expenseId)),
    calcPending: true,
    error: null,
  };
  if (Number(state.closingEditingExpenseId) === Number(expenseId)) {
    state.closingEditingExpenseId = null;
  }
  renderClosingPanelFromCache();
  scheduleClosingCalculationRefresh();
  return true;
}

function updateClosingExpenseInCache(expense) {
  if (!expense) return false;
  const current = state.closingPanelData && state.closingPanelData.month === state.month
    ? state.closingPanelData
    : null;
  if (!current) return false;

  state.closingPanelData = {
    ...current,
    expenses: (current.expenses || []).map((item) => (
      Number(item.id) === Number(expense.id) ? expense : item
    )),
    calcPending: true,
    error: null,
  };
  state.closingEditingExpenseId = null;
  renderClosingPanelFromCache();
  scheduleClosingCalculationRefresh();
  return true;
}

function startClosingExpenseEdit(expenseId) {
  state.closingEditingExpenseId = Number(expenseId);
  renderClosingPanelFromCache();
  setTimeout(() => {
    const input = document.querySelector(`[data-edit-expense-amount-id="${expenseId}"]`);
    if (input) {
      input.focus();
      input.select();
    }
  }, 0);
}

function cancelClosingExpenseEdit() {
  state.closingEditingExpenseId = null;
  renderClosingPanelFromCache();
}

async function saveClosingExpenseAmount(expenseId, button = null) {
  const input = document.querySelector(`[data-edit-expense-amount-id="${expenseId}"]`);
  const amount = normalizeNumberInput(input?.value || 0);

  if (amount <= 0) {
    alert("Укажите сумму расхода.");
    input?.focus();
    return;
  }

  try {
    setButtonLoading(button, true, "…");
    const updatedExpense = await api(`/monthly-expenses/${expenseId}`, {
      method: "PATCH",
      body: JSON.stringify({ amount: String(Math.round(amount * 100) / 100) }),
    });
    if (!updateClosingExpenseInCache(updatedExpense)) {
      state.closingEditingExpenseId = null;
      markClosingCalculationPending();
    }
  } finally {
    setButtonLoading(button, false);
  }
}

function attachClosingExpenseFormKeyboard() {
  const titleInput = document.getElementById("closingExpenseTitle");
  const amountInput = document.getElementById("closingExpenseAmount");

  titleInput?.addEventListener("keydown", (event) => {
    if (event.key === "ArrowRight" || event.key === "Enter") {
      event.preventDefault();
      amountInput?.focus();
      amountInput?.select();
    }
  });

  amountInput?.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      titleInput?.focus();
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      addClosingExpense().catch((error) => alert(error.message));
    }
  });
}

async function addClosingExpense() {
  const titleInput = document.getElementById("closingExpenseTitle");
  const amountInput = document.getElementById("closingExpenseAmount");
  const allocationInput = document.getElementById("closingExpenseAllocation");
  const commentInput = document.getElementById("closingExpenseComment");
  const sanzharInput = document.getElementById("closingExpenseSanzhar");
  const raufalInput = document.getElementById("closingExpenseRaufal");

  const title = String(titleInput?.value || "").trim();
  const amount = normalizeNumberInput(amountInput?.value || 0);
  const allocationType = allocationInput?.value || "default_split";

  if (!title) {
    alert("Укажите название расхода.");
    titleInput?.focus();
    return;
  }
  if (amount <= 0) {
    alert("Укажите сумму расхода.");
    amountInput?.focus();
    return;
  }

  const payload = {
    month: closingMonthDate(),
    title,
    amount: String(Math.round(amount * 100) / 100),
    allocation_type: allocationType,
    comment: String(commentInput?.value || "").trim() || null,
    created_by_user_id: state.bootstrap?.user?.id || null,
  };

  if (allocationType === "custom") {
    payload.sanzhar_amount = String(Math.round(normalizeNumberInput(sanzharInput?.value || 0) * 100) / 100);
    payload.raufal_amount = String(Math.round(normalizeNumberInput(raufalInput?.value || 0) * 100) / 100);
  }

  const button = document.getElementById("addClosingExpenseBtn");
  try {
    setButtonLoading(button, true, "Сохраняем…");
    const createdExpense = await api("/monthly-expenses", { method: "POST", body: JSON.stringify(payload) });
    clearClosingExpenseForm();
    if (!insertClosingExpenseIntoCache(createdExpense)) {
      markClosingCalculationPending();
    }
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(button, false);
  }
}

async function deleteClosingExpense(expenseId, button = null) {
  if (!window.confirm("Удалить расход?")) return;
  try {
    setButtonLoading(button, true, "…");
    await api(`/monthly-expenses/${expenseId}`, { method: "DELETE" });
    if (!removeClosingExpenseFromCache(expenseId)) {
      markClosingCalculationPending();
    }
  } finally {
    setButtonLoading(button, false);
  }
}

async function closeSelectedMonth() {
  if (!window.confirm(`Закрыть ${monthLabelRu(state.month)}? Это сохранит текущую калькуляцию, но мероприятия останутся редактируемыми.`)) return;
  await withLoading(async () => {
    await api(`/monthly-closings/close?month=${state.month}`, { method: "POST" });
    await loadDashboard();
  }, "Закрываем месяц…");
}

async function reopenSelectedMonth() {
  if (!window.confirm(`Открыть ${monthLabelRu(state.month)} заново?`)) return;
  await withLoading(async () => {
    await api(`/monthly-closings/reopen?month=${state.month}`, { method: "POST" });
    await loadDashboard();
  }, "Открываем месяц…");
}

async function recalculateSelectedMonthClosing() {
  const existingClosing = await loadClosingByMonth(state.month);
  const isClosed = existingClosing?.status === "closed";

  if (!isClosed) {
    await withLoading(async () => {
      await refreshClosingPanel({ includeCalculation: true });
    }, "Пересчитываем…");
    return;
  }

  if (!window.confirm(`Пересчитать и обновить закрытие ${monthLabelRu(state.month)}? Snapshot закрытого месяца будет перезаписан текущими расходами и фактами.`)) return;

  await withLoading(async () => {
    await api(`/monthly-closings/close?month=${state.month}`, { method: "POST" });
    await loadDashboard();
  }, "Пересчитываем закрытый месяц…");
}

function attachClosingPanelEvents() {
  const panel = document.getElementById("closingPanel");
  if (!panel || panel.dataset.eventsAttached === "1") return;
  panel.dataset.eventsAttached = "1";

  document.getElementById("closingExpenseAllocation")?.addEventListener("change", setClosingCustomSplitVisibility);
  document.getElementById("addClosingExpenseBtn")?.addEventListener("click", addClosingExpense);
  attachClosingExpenseFormKeyboard();
  document.getElementById("recalculateClosingBtn")?.addEventListener("click", () => {
    recalculateSelectedMonthClosing().catch((error) => alert(error.message));
  });
  document.getElementById("closeMonthBtn")?.addEventListener("click", () => closeSelectedMonth().catch((error) => alert(error.message)));
  document.getElementById("reopenClosingBtn")?.addEventListener("click", () => reopenSelectedMonth().catch((error) => alert(error.message)));
  document.querySelectorAll("[data-edit-expense-id]").forEach((button) => {
    button.addEventListener("click", () => startClosingExpenseEdit(button.dataset.editExpenseId));
  });
  document.querySelectorAll("[data-save-expense-id]").forEach((button) => {
    button.addEventListener("click", () => saveClosingExpenseAmount(button.dataset.saveExpenseId, button).catch((error) => alert(error.message)));
  });
  document.querySelectorAll("[data-cancel-edit-expense-id]").forEach((button) => {
    button.addEventListener("click", cancelClosingExpenseEdit);
  });
  document.querySelectorAll("[data-edit-expense-amount-id]").forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const saveButton = document.querySelector(`[data-save-expense-id="${input.dataset.editExpenseAmountId}"]`);
        saveClosingExpenseAmount(input.dataset.editExpenseAmountId, saveButton).catch((error) => alert(error.message));
      }
      if (event.key === "Escape") {
        event.preventDefault();
        cancelClosingExpenseEdit();
      }
    });
  });
  document.querySelectorAll("[data-delete-expense-id]").forEach((button) => {
    button.addEventListener("click", () => deleteClosingExpense(button.dataset.deleteExpenseId, button).catch((error) => alert(error.message)));
  });

  setClosingCustomSplitVisibility();
}

async function attachClosingPanel() {
  const panel = document.getElementById("closingPanel");
  if (!panel || panel.dataset.loading === "1" || panel.dataset.loaded === "1") return;
  panel.dataset.loading = "1";
  await refreshClosingPanel();
  panel.dataset.loading = "0";
  panel.dataset.loaded = "1";
}

async function ensureMonthlyPlansLoadedForEditor() {
  const editor = document.getElementById("plansEditor");
  if (!editor) return false;

  const year = Number(editor.dataset.plansYear || planEditorYear());
  if (Number(state.monthlyPlansYear) === year) return true;

  try {
    const plans = await api(`/monthly-plans?_=${Date.now()}`);
    state.monthlyPlans = Array.isArray(plans) ? plans : [];
    state.monthlyPlansYear = year;
  } catch (error) {
    editor.innerHTML = `<div class="empty-state">Не удалось загрузить планы: ${escapeHtml(error.message)}</div>`;
    return false;
  }

  const content = document.getElementById("dashboardContent");
  if (content && state.activeAdminTab === "plans") {
    content.innerHTML = renderPlansSkeleton(state.adminData || emptyAdminDashboard(state.month));
    attachPlansModal();
  }

  return false;
}

function planPercentInput(monthValue, kind) {
  return document.querySelector(`[data-plan-percent="${kind}"][data-plan-month="${monthValue}"]`);
}

function setMirroredDepartmentPercent(changedInput) {
  if (!changedInput) return;
  const monthValue = changedInput.dataset.planMonth;
  const kind = changedInput.dataset.planPercent;
  if (!monthValue || !["sanzhar", "raufal"].includes(kind)) return;

  const mirroredKind = kind === "sanzhar" ? "raufal" : "sanzhar";
  const mirroredInput = planPercentInput(monthValue, mirroredKind);
  if (!mirroredInput) return;

  const value = Math.max(0, Math.min(100, normalizeNumberInput(changedInput.value)));
  changedInput.value = formatPercentValue(value);
  mirroredInput.value = formatPercentValue(100 - value);
}

function updatePlansCalculatedCells() {
  document.querySelectorAll("[data-month-plan-input]").forEach((input) => {
    const monthValue = input.dataset.monthPlanInput;
    const companyPlan = normalizeNumberInput(input.value);
    const sanzharPercent = normalizeNumberInput(planPercentInput(monthValue, "sanzhar")?.value || 0);
    const raufalPercent = normalizeNumberInput(planPercentInput(monthValue, "raufal")?.value || 0);
    const managerPercent = normalizeNumberInput(planPercentInput(monthValue, "manager")?.value || 0);

    const sanzharCell = document.querySelector(`[data-plan-calc-sanzhar="${monthValue}"]`);
    const raufalCell = document.querySelector(`[data-plan-calc-raufal="${monthValue}"]`);
    const managerCell = document.querySelector(`[data-plan-calc-manager="${monthValue}"]`);

    if (sanzharCell) sanzharCell.textContent = formatMoney(companyPlan * sanzharPercent / 100);
    if (raufalCell) raufalCell.textContent = formatMoney(companyPlan * raufalPercent / 100);
    if (managerCell) managerCell.textContent = formatMoney(companyPlan * managerPercent / 100);
  });
}

async function savePlansYear() {
  const button = document.getElementById("savePlansYearBtn");
  const message = document.getElementById("plansSaveMessage");
  const year = planEditorYear();
  const inputs = [...document.querySelectorAll("[data-month-plan-input]")];
  const rows = [];

  for (const input of inputs) {
    const monthValue = input.dataset.monthPlanInput;
    const sanzharPercent = normalizeNumberInput(planPercentInput(monthValue, "sanzhar")?.value || 0);
    const raufalPercent = normalizeNumberInput(planPercentInput(monthValue, "raufal")?.value || 0);
    const managerPercent = normalizeNumberInput(planPercentInput(monthValue, "manager")?.value || 0);
    const monthLabel = MONTHS_RU.find(([value]) => value === monthValue)?.[1] || monthValue;

    if (Math.abs((sanzharPercent + raufalPercent) - 100) > 0.01) {
      alert(`Сумма процентов Санжар и Рауфаль за ${monthLabel} должна быть 100%.`);
      return;
    }

    if (managerPercent < 0 || managerPercent > 100) {
      alert(`Процент плана менеджера за ${monthLabel} должен быть от 0 до 100.`);
      return;
    }

    rows.push({
      month: planMonthDate(year, monthValue),
      company_plan_amount: String(Math.round(normalizeNumberInput(input.value) * 100) / 100),
      sanzhar_share_percent: String(Math.round(sanzharPercent * 100) / 100),
      raufal_share_percent: String(Math.round(raufalPercent * 100) / 100),
      manager_personal_plan_percent: String(Math.round(managerPercent * 100) / 100),
    });
  }

  try {
    setButtonLoading(button, true, "Сохраняем…");
    if (message) message.textContent = "Сохраняем 12 месяцев…";

    for (const payload of rows) {
      await api("/monthly-plans", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }

    state.monthlyPlansYear = null;
    if (message) message.textContent = "Планы сохранены.";
    await loadDashboard();
  } catch (error) {
    if (message) message.textContent = error.message;
    else alert(error.message);
  } finally {
    setButtonLoading(button, false);
  }
}


async function deleteManagerFromSystem(managerId, managerName) {
  const name = managerName || "менеджера";
  const ok = window.confirm(`Удалить ${name} до конца месяца? Кабинет менеджера сразу заблокируется. В обзоре текущего месяца он останется серым и его можно будет восстановить.`);
  if (!ok) return;

  await withLoading(async () => {
    await api(`/users/${managerId}`, { method: "DELETE" });
    await loadDashboard();
  }, "Удаляем менеджера…");
}

async function restoreManagerInSystem(managerId, managerName) {
  const name = managerName || "менеджера";
  const ok = window.confirm(`Восстановить ${name}? Кабинет менеджера снова станет доступен.`);
  if (!ok) return;

  await withLoading(async () => {
    await api(`/users/${managerId}/restore`, { method: "POST" });
    await loadDashboard();
  }, "Восстанавливаем менеджера…");
}

function attachManagerDeleteButtons() {
  document.querySelectorAll("[data-delete-manager-id]").forEach((button) => {
    if (button.dataset.attached === "1") return;
    button.dataset.attached = "1";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      deleteManagerFromSystem(button.dataset.deleteManagerId, button.dataset.deleteManagerName).catch((error) => alert(error.message));
    });
  });

  document.querySelectorAll("[data-restore-manager-id]").forEach((button) => {
    if (button.dataset.attached === "1") return;
    button.dataset.attached = "1";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      restoreManagerInSystem(button.dataset.restoreManagerId, button.dataset.restoreManagerName).catch((error) => alert(error.message));
    });
  });
}

async function attachPlansModal() {
  const editor = document.getElementById("plansEditor");
  if (!editor) return;

  const loaded = await ensureMonthlyPlansLoadedForEditor();
  if (!loaded) return;

  document.querySelectorAll('[data-plan-percent="sanzhar"], [data-plan-percent="raufal"]').forEach((input) => {
    input.addEventListener("input", () => {
      setMirroredDepartmentPercent(input);
      updatePlansCalculatedCells();
    });
    input.addEventListener("blur", () => {
      setMirroredDepartmentPercent(input);
      updatePlansCalculatedCells();
    });
  });

  document.querySelectorAll('[data-plan-percent="manager"]').forEach((input) => {
    input.addEventListener("input", updatePlansCalculatedCells);
    input.addEventListener("blur", () => {
      const value = Math.max(0, Math.min(100, normalizeNumberInput(input.value)));
      input.value = formatPercentValue(value);
      updatePlansCalculatedCells();
    });
  });

  document.querySelectorAll("[data-month-plan-input]").forEach((input) => {
    input.addEventListener("input", updatePlansCalculatedCells);
    input.addEventListener("blur", () => {
      input.value = formatInputNumber(input.value);
      updatePlansCalculatedCells();
    });
  });

  const saveButton = document.getElementById("savePlansYearBtn");
  if (saveButton) saveButton.addEventListener("click", savePlansYear);

  updatePlansCalculatedCells();
}


async function loadUsersForAdmin() {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return;

  try {
    state.users = await api("/users?include_inactive=true");
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
    const dashboard = await api(`/department-head-dashboard?department_id=${user.department_id}&month=${month}&include_drafts=true&_=${Date.now()}`);
    renderDepartmentDashboard(dashboard);
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

  resetEventModalModes();
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
  state.adminEventEditModeId = null;
  $("eventModalBackdrop").classList.add("hidden");
  $("eventModalBackdrop").classList.remove("pin-modal-mode");
  $("eventModalBackdrop").classList.remove("profile-modal-mode");
  $("eventModalBackdrop").classList.remove("payment-modal-mode");
  $("eventModalBackdrop").classList.remove("admin-event-edit-mode");
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
