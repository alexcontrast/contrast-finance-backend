const state = {
  token: localStorage.getItem("cf_token") || "",
  bootstrap: null,
  month: new Date().toISOString().slice(0, 7),
  paymentStatusFilter: "active",
  paymentSearch: "",
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
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(n).replace(/,00$/, "");
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
  return event?.status === "draft";
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
  return `<span class="mini-pill"><strong>${label}:</strong> ${value}</span>`;
}

function normalizeNumberInput(value) {
  const cleaned = String(value || "").replace(/\s/g, "").replace(",", ".");
  const number = Number(cleaned);
  return Number.isFinite(number) ? number : 0;
}

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


function showLogin() {
  $("loginScreen").classList.remove("hidden");
  $("dashboardScreen").classList.add("hidden");
  $("logoutBtn").classList.add("hidden");
  $("userBadge").classList.add("hidden");
  $("adminTabs").classList.add("hidden");
  $("pageTitle").textContent = "Вход";
  $("pageSubtitle").textContent = "Финансовая панель мероприятий";
}

function showDashboardShell() {
  $("loginScreen").classList.add("hidden");
  $("dashboardScreen").classList.remove("hidden");
  $("logoutBtn").classList.remove("hidden");
  $("userBadge").classList.remove("hidden");
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

  const search = String(state.paymentSearch || "").trim().toLowerCase();
  if (search) {
    list = list.filter((request) => String(clientNameForRequest(request) || "").toLowerCase().includes(search));
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
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Дата</th><th>Заказчик</th><th>Мероприятие</th><th>Менеджер</th><th>Статус</th>
            <th>Оборот</th><th>Доход</th><th>ЗП менеджера</th><th>Заявки</th>
          </tr>
        </thead>
        <tbody>
          ${events.map((event) => `
            <tr class="${allowClick ? "clickable-row" : ""} ${departmentClassById(event.department_id)}" ${allowClick ? `data-event-id="${event.id}"` : ""}>
              <td class="nowrap">${event.event_date || ""}</td>
              <td><strong>${event.client_name || ""}</strong></td>
              <td>${event.title || ""}</td>
              <td>${event.manager_name || managerNameById(event.manager_id) || ""}</td>
              <td><span class="status ${event.status}">${statusLabel(event.status)}</span></td>
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

function renderPaymentFilters(mode = "regular") {
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

      <label class="compact-label search-label">Поиск по заказчику
        <input id="paymentSearch" value="${state.paymentSearch || ""}" placeholder="Название заказчика" />
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

function renderPaymentRequestsTable(requests, title = "Заявки на оплату", mode = "regular") {
  const baseRequests = mode === "archive" ? archivedPaymentRequests(requests) : activePaymentRequests(requests);
  const filteredRequests = filteredPaymentRequests(requests, mode);

  if (!baseRequests.length) {
    return `
      <div class="block-title"><h3>${title}</h3></div>
      ${renderPaymentFilters(mode)}
      <div class="empty-state">Заявок пока нет.</div>
    `;
  }

  if (!filteredRequests.length) {
    return `
      <div class="block-title">
        <h3>${title}</h3>
        <span class="muted">0 из ${baseRequests.length} шт.</span>
      </div>
      ${renderPaymentFilters(mode)}
      <div class="empty-state">По выбранным фильтрам заявок нет.</div>
    `;
  }

  return `
    <div class="block-title">
      <h3>${title}</h3>
      <span class="muted">${filteredRequests.length} из ${baseRequests.length} шт.</span>
    </div>
    ${renderPaymentFilters(mode)}
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
    paymentStatus.addEventListener("change", async (event) => {
      state.paymentStatusFilter = event.target.value;
      await withLoading(loadDashboard, "Фильтруем заявки…");
    });
  }

  const paymentSearch = document.getElementById("paymentSearch");
  if (paymentSearch) {
    paymentSearch.addEventListener("input", (event) => {
      state.paymentSearch = event.target.value;
      clearTimeout(window.__cfPaymentSearchTimer);
      window.__cfPaymentSearchTimer = setTimeout(() => {
        withLoading(loadDashboard, "Ищем…").catch((error) => alert(error.message));
      }, 350);
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

function renderAdminDashboard(data) {
  state.adminData = data;
  renderAdminTabs();

  renderSummary([]);

  $("dashboardTitle").textContent = "Админка";
  $("dashboardHint").textContent = "Скелет вкладок v0.30";

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

function renderManagerEventList(data) {
  const events = data.events || [];
  const selected = getSelectedManagerEvent(data);

  return `
    <aside class="manager-sidebar-card">
      <h3>Мероприятия</h3>
      <p class="muted">Проекты за выбранный месяц</p>


      <div class="manager-mini-list">
        ${events.length ? events.map((event) => `
          <button class="manager-mini-card ${Number(selected?.id) === Number(event.id) ? "active" : ""}" data-manager-event-id="${event.id}">
            <div class="mini-card-pills">
              ${managerCardMetric("Бюджет", formatMoney(event.external_total || 0))}
              ${managerCardMetric("Доход", formatMoney(event.final_company_income || 0))}
            </div>
            <strong>${event.title || "Без названия"}</strong>
            <span>${event.client_name || ""} · ${formatDateRu(event.event_date)}</span>
            <small>${customerPaymentLabel(event.client_calc_type)}</small>
            <em>${statusLabel(event.status)}</em>
          </button>
        `).join("") : `<div class="empty-state">Мероприятий пока нет.</div>`}
      </div>
    </aside>
  `;
}

async function renderManagerEventDetail(eventId, options = {}) {
  const holder = document.getElementById("managerEventDetail");
  if (!holder) return;

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

    const draftEvent = getDraftEvent(event);
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
  const taxes = Math.round(clientBase * taxRate / 100);
  const taxesNet = taxes - deductions;

  const vatNet = Math.max(0, clientVat - contractorVatCredit);

  const regularCommission = regularExternal - regularFact;
  const managerBase = regularCommission + agency + simplifiedMarkup + contractorVatCredit + deductions - taxes;
  const managerSalary = managerBase > 0 ? Math.round(managerBase * asNumber(event?.manager_percent || 21) / 100) : 0;
  const companyIncome = managerBase - managerSalary + coordinatorCompanyShare;

  return {
    ...(backendSummary || {}),
    turnover_with_vat: turnover,
    external_total: turnover,
    agency_commission_amount: agency,
    client_vat_amount: clientVat,
    contractor_vat_credit: contractorVatCredit,
    deductions_total: deductions,
    taxes_total: taxes,
    taxes_net: taxesNet,
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

  if (["external_price", "external_quantity", "external_days", "amount_fact"].includes(field)) {
    item[field] = value === "" ? null : normalizeNumberInput(value);
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
      const base = asNumber(item.amount_fact) > 0 ? asNumber(item.amount_fact) : externalRowAmount(item);
      item.vat_amount = 0;
      item.deduction_amount = Math.round(base * 0.10);
      item.iin_bin_locked = false;
    }
  }

  if (["external_price", "external_quantity", "external_days"].includes(field) && item.item_type === "coordinator") {
    item.amount_fact = Math.round(externalRowAmount(item) * 0.5);
  }

  if (field === "amount_fact" && item.payment_method === "self_employed") {
    const base = asNumber(item.amount_fact) > 0 ? asNumber(item.amount_fact) : externalRowAmount(item);
    item.deduction_amount = Math.round(base * 0.10);
  }
}


function attachDraftEventInputs(eventId) {
  document.querySelectorAll("[data-event-field]").forEach((input) => {
    input.addEventListener("input", () => {
      setDraftEventValue(eventId, input.getAttribute("data-event-field"), input.value);
      refreshDraftVisibleCalculations(eventId);
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

  await api(`/events/${eventId}`, {
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
}

function attachDraftInputs(eventId) {
  document.querySelectorAll("[data-item-field]").forEach((input) => {
    input.addEventListener("input", () => {
      setDraftItemValue(eventId, input.getAttribute("data-item-id"), input.getAttribute("data-item-field"), input.value);
      refreshDraftVisibleCalculations(eventId);
    });

    input.addEventListener("change", () => {
      setDraftItemValue(eventId, input.getAttribute("data-item-id"), input.getAttribute("data-item-field"), input.value);
      renderManagerEventDetail(eventId, { useDraft: true, noLoading: true });
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

function isCoordinatorItem(item) {
  return item.item_type === "coordinator";
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
  return estimateInputMoney(item.amount_fact);
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
    external_name: "Новая позиция",
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
            <tr data-event-item-row="${item.id}">
              <td class="drag-col">${draggableHandle(item)}</td>
              <td>${rowInput(item.external_name, `data-item-field="external_name" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(formatMoney(item.external_price), `data-item-field="external_price" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(item.external_quantity || 1, `data-item-field="external_quantity" data-item-id="${item.id}"`)}</td>
              <td>${rowInput(item.external_days || 1, `data-item-field="external_days" data-item-id="${item.id}"`)}</td>
              <td><strong data-row-sum>${formatMoney(externalRowAmount(item))}</strong></td>
              <td>${rowInput(item.external_note || "", `placeholder="Примечание для клиента" data-item-field="external_note" data-item-id="${item.id}"`)}</td>
              <td>${item.item_type === "coordinator" ? "" : `<button class="icon-btn danger" data-delete-item="${item.id}">×</button>`}</td>
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
            const binDisabled = isCoordinatorItem(item) || item.payment_method !== "invoice";
            return `
              <tr data-event-item-row="${item.id}">
                <td class="drag-col">${draggableHandle(item)}</td>
                <td>${rowInput(item.external_name, `data-item-field="external_name" data-item-id="${item.id}"`)}</td>
                <td><strong>${formatMoney(externalRowAmount(item))}</strong></td>
                <td>${rowInput(internalFactDisplayValue(item), `data-item-field="amount_fact" data-item-id="${item.id}" ${item.item_type === "coordinator" ? "disabled" : ""}`)}</td>
                <td>
                  ${isCoordinatorItem(item) ? `
                    <select disabled>
                      <option selected>—</option>
                    </select>
                  ` : `
                    <select data-item-field="payment_method" data-item-id="${item.id}">
                      <option value="" ${!item.payment_method ? "selected" : ""}>—</option>
                      <option value="cash" ${item.payment_method === "cash" ? "selected" : ""}>Налик</option>
                      <option value="card" ${item.payment_method === "card" ? "selected" : ""}>На карту</option>
                      <option value="self_employed" ${item.payment_method === "self_employed" ? "selected" : ""}>Самозанятый</option>
                      <option value="invoice" ${item.payment_method === "invoice" ? "selected" : ""}>По счету</option>
                    </select>
                  `}
                </td>
                <td>${rowInput(binDisabled ? "" : (item.iin_bin || ""), `placeholder="12 цифр" ${binDisabled ? "disabled" : `data-item-field="iin_bin" data-item-id="${item.id}" ${item.iin_bin_locked ? "disabled" : ""}`}`)}</td>
                <td>
                  ${isCoordinatorItem(item) ? "—" : (item.payment_method === "invoice" ? `
                    <button class="icon-btn" data-check-tax-item="${item.id}" title="${item.iin_bin_locked ? "Изменить BIN" : "Проверить КГД"}">
                      ${item.iin_bin_locked ? "✎" : "✓"}
                    </button>
                  ` : "—")}
                </td>
                <td class="vat-col"><strong>${formatMoney(internalVatValue(item))}</strong></td>
                <td class="deduction-col"><strong>${formatMoney(internalDeductionValue(item))}</strong></td>
                <td class="commission-col"><strong>${formatMoney(internalCommissionValue(item))}</strong></td>
                <td class="paid-col"><strong>${formatMoney(item.paid_amount)}</strong></td>
                <td>${item.item_type === "coordinator" ? "" : `<button class="icon-btn danger" data-delete-item="${item.id}">×</button>`}</td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderManagerEventCard(event, items = [], summary = null) {
  const activeTab = state.managerEstimateTab || "external";

  return `
    <section class="manager-event-card">
      <div class="manager-event-head">
        <div>
          <div class="overview-label">Карточка мероприятия</div>
          <h2>${event.title}</h2>
          <span class="status ${event.status}">${statusLabel(event.status)}</span>
        </div>
        <div class="inline-actions">
          <button class="secondary" disabled>Оплатить</button>
          <button class="ghost" disabled>Передать</button>
          <button class="ghost" disabled>Соавтор</button>
        </div>
      </div>

      <div class="manager-event-fields">
        <label>Тип расчёта с заказчиком
          <select data-event-field="client_calc_type" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"}>
            <option value="ip_contrast_event" ${event.client_calc_type === "ip_contrast_event" ? "selected" : ""}>ИП Contrast Event</option>
            <option value="our_no_vat" ${event.client_calc_type === "our_no_vat" ? "selected" : ""}>ОУР без НДС</option>
            <option value="simplified" ${event.client_calc_type === "simplified" ? "selected" : ""}>Упрощенка</option>
            <option value="cash" ${event.client_calc_type === "cash" ? "selected" : ""}>Нал</option>
          </select>
        </label>
        <label>Дата мероприятия
          <input type="date" value="${eventDateForInput(event.event_date)}" data-event-field="event_date" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"} />
        </label>
        <label>Название заказчика
          <input value="${event.client_name || ""}" data-event-field="client_name" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"} />
        </label>
        <label>Название мероприятия
          <input value="${event.title || ""}" data-event-field="title" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"} />
        </label>
        <label>Комиссия агентства, %
          <input value="${formatMoney(event.agency_commission_amount || 0)}" data-event-field="agency_commission_amount" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"} />
        </label>
        ${event.client_calc_type === "simplified" ? `
          <label>Банк+налоги, %
            <input value="${formatPlainNumber(event.simplified_bank_tax_percent || 0)}" data-event-field="simplified_bank_tax_percent" data-event-id="${event.id}" ${isDraftEvent(event) ? "" : "disabled"} />
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
        <button class="save-draft-btn" data-manager-event-save-draft="${event.id}">Сохранить черновик</button>
        <button data-manager-event-send-review="${event.id}">Отправить Саше</button>
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
  const isCoordinator = item.item_type === "coordinator";
  const coordinatorFact = Math.round(externalRowAmount(item) * 0.5);

  return {
    item_type: item.item_type || "regular",
    external_name: item.external_name || "",
    external_price: asNumber(item.external_price),
    external_quantity: asNumber(item.external_quantity || 1),
    external_days: asNumber(item.external_days || 1),
    external_note: item.external_note || null,
    amount_fact: isCoordinator ? coordinatorFact : (item.amount_fact === "" || item.amount_fact === undefined ? null : item.amount_fact),
    paid_amount: item.paid_amount || 0,
    payment_method: isCoordinator ? null : (item.payment_method || null),
    iin_bin: isCoordinator || item.payment_method !== "invoice" ? null : (item.iin_bin || null),
    iin_bin_locked: isCoordinator || item.payment_method !== "invoice" ? false : (item.iin_bin_locked || false),
    tax_check_status: isCoordinator || item.payment_method !== "invoice" ? null : (item.tax_check_status || null),
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
      await api(`/events/${eventId}/items`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } else {
      await api(`/event-items/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    }
  }

  delete state.managerDraftItemsByEventId[draftKeyForEvent(eventId)];
  delete state.managerDraftDeletedByEventId[draftKeyForEvent(eventId)];
  if (state.managerDraftEventsById) delete state.managerDraftEventsById[String(eventId)];
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

  state.managerDraftItemsByEventId[draftKeyForEvent(eventId)] = items.filter((candidate) => String(candidate.id) !== String(itemId));
  if (!String(itemId).startsWith("tmp-")) {
    getDraftDeletedIds(eventId).push(itemId);
  }
}

async function checkTaxForItem(itemId) {
  const input = document.querySelector(`[data-item-field="iin_bin"][data-item-id="${itemId}"]`);
  const iinBin = input?.value?.trim();

  if (!iinBin) {
    alert("Сначала укажи БИН/ИИН");
    return;
  }

  if (String(itemId).startsWith("tmp-")) {
    alert("Сначала нажми “Сохранить черновик”, потом проверяй КГД по новой позиции");
    return;
  }

  await api(`/event-items/${itemId}/tax/check`, {
    method: "POST",
    body: JSON.stringify({ iin_bin: iinBin }),
  });

  delete state.managerDraftItemsByEventId[draftKeyForEvent(state.selectedManagerEventId)];
}

function attachManagerCreateWorkspaceActions() {
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
      addDraftRegularPosition(state.selectedManagerEventId);
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });

  document.querySelectorAll("[data-delete-item]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!confirm("Удалить позицию?")) return;
      deleteDraftItem(state.selectedManagerEventId, button.getAttribute("data-delete-item"));
      renderManagerEventDetail(state.selectedManagerEventId, { useDraft: true, noLoading: true });
    });
  });

  document.querySelectorAll("[data-check-tax-item]").forEach((button) => {
    button.addEventListener("click", async () => {
      const itemId = button.getAttribute("data-check-tax-item");
      await withLoading(async () => {
        await saveDraftItems(state.selectedManagerEventId);
        await checkTaxForItem(itemId);
        await renderManagerEventDetail(state.selectedManagerEventId);
        await loadDashboard();
      }, "Проверяем КГД…");
    });
  });

  document.querySelectorAll("[data-manager-event-save-draft]").forEach((button) => {
    button.addEventListener("click", async () => {
      const eventId = button.getAttribute("data-manager-event-save-draft");
      await withLoading(async () => {
        await saveDraftEvent(eventId);
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "draft");
        await renderManagerEventDetail(eventId);
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
        await saveDraftEvent(eventId);
        await saveDraftItems(eventId);
        await updateManagerEventStatus(eventId, "review");
        await renderManagerEventDetail(eventId);
        await loadDashboard();
      }, "Отправляем на проверку…");
    });
  });


  attachEstimateKeyboardNavigation();
  attachEstimateDragAndDrop();
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
        await renderManagerEventDetail(eventId);
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
        await renderManagerEventDetail(eventId);
        await loadDashboard();
      }, "Отправляем на проверку…");
    });
  });

}
function renderManagerDashboard(data, paymentRequests = []) {
  state.managerData = data;
  state.managerPaymentRequests = paymentRequests || [];

  $("adminTabs").classList.add("hidden");
  renderSummary([]);

  $("dashboardTitle").textContent = "Мои мероприятия";
  $("dashboardHint").textContent = "";

  $("dashboardContent").innerHTML = renderManagerDashboardLayout(data);

  attachPaymentRequestActions();
  attachManagerDashboardActions();

  const selected = getSelectedManagerEvent(data);
  if (selected) {
    state.selectedManagerEventId = selected.id;
    renderManagerEventDetail(selected.id);
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
    await loadUsersForAdmin();
    renderAdminDashboard(await api(`/admin-dashboard?month=${month}&include_drafts=true`));
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

  const [dashboard, requests] = await Promise.all([
    api(`/manager-dashboard?month=${month}&include_drafts=true`),
    api("/payment-requests"),
  ]);
  renderManagerDashboard(dashboard, requests);
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
    $("pageTitle").textContent = roleLabel(user.role);
    $("pageSubtitle").textContent = user.role === "admin"
      ? "Проверка мероприятий, заявки, планы и закрытие месяца"
      : `${user.name} · отдел ${departmentNameById(user.department_id) || ""}`;
    $("userBadge").textContent = `${user.name} · ${roleLabel(user.role)}`;

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
  $("loginError").classList.add("hidden");

  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        name: $("loginName").value || null,
        phone: null,
        pin: $("loginPin").value,
      }),
    });

    state.token = data.access_token;
    localStorage.setItem("cf_token", state.token);
    await boot();
  } catch (error) {
    $("loginError").textContent = error.message;
    $("loginError").classList.remove("hidden");
  }
}

async function changePin() {
  const msg = $("changePinMessage");
  msg.textContent = "";

  try {
    const data = await api("/auth/change-pin", {
      method: "PATCH",
      body: JSON.stringify({
        old_pin: $("oldPin").value,
        new_pin: $("newPin").value,
      }),
    });

    msg.textContent = data.message || "PIN изменён";
    $("oldPin").value = "";
    $("newPin").value = "";
  } catch (error) {
    msg.textContent = error.message;
  }
}

$("loginBtn").addEventListener("click", login);
$("loginPin").addEventListener("keydown", (event) => {
  if (event.key === "Enter") login();
});

$("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("cf_token");
  state.token = "";
  state.bootstrap = null;
  showLogin();
});

$("reloadBtn").addEventListener("click", () => {
  withLoading(loadDashboard, "Обновляем данные…").catch((error) => alert(error.message));
});

$("changePinOpenBtn").addEventListener("click", () => {
  $("changePinCard").classList.toggle("hidden");
});

$("changePinBtn").addEventListener("click", changePin);

$("eventModalCloseBtn").addEventListener("click", () => {
  $("eventModalBackdrop").classList.add("hidden");
});

$("plansModalCloseBtn").addEventListener("click", () => {
  $("plansModalBackdrop").classList.add("hidden");
});

boot();