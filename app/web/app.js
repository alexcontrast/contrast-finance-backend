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
  adminData: null,
  users: [],
};

const $ = (id) => document.getElementById(id);

function formatMoney(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n);
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

function filteredPaymentRequests(requests) {
  let list = [...(requests || [])];

  if (state.paymentStatusFilter === "active") {
    list = list.filter((request) => !["rejected", "cash_received"].includes(request.status));
  } else if (state.paymentStatusFilter !== "all") {
    list = list.filter((request) => request.status === state.paymentStatusFilter);
  }

  const search = String(state.paymentSearch || "").trim().toLowerCase();
  if (search) {
    list = list.filter((request) => String(request.client_name || "").toLowerCase().includes(search));
  }

  return list;
}

function renderAdminTabs() {
  const tabs = [
    ["overview", "Обзор"],
    ["events", "Мероприятия"],
    ["requests", "Заявки"],
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
      renderAdminDashboard(state.adminData);
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

function renderPaymentFilters() {
  return `
    <div class="filters-row">
      <label class="compact-label">Статус оплаты
        <select id="paymentStatusFilter">
          <option value="active" ${state.paymentStatusFilter === "active" ? "selected" : ""}>Активные</option>
          <option value="all" ${state.paymentStatusFilter === "all" ? "selected" : ""}>Все</option>
          <option value="new" ${state.paymentStatusFilter === "new" ? "selected" : ""}>Новая</option>
          <option value="paid" ${state.paymentStatusFilter === "paid" ? "selected" : ""}>Оплачено</option>
          <option value="cash_received" ${state.paymentStatusFilter === "cash_received" ? "selected" : ""}>Деньги в кассе</option>
          <option value="rejected" ${state.paymentStatusFilter === "rejected" ? "selected" : ""}>Отменено</option>
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

function renderPaymentRequestsTable(requests, title = "Заявки на оплату") {
  const filteredRequests = filteredPaymentRequests(requests);

  if (!requests || !requests.length) {
    return `
      <div class="block-title"><h3>${title}</h3></div>
      ${renderPaymentFilters()}
      <div class="empty-state">Заявок пока нет.</div>
    `;
  }

  if (!filteredRequests.length) {
    return `
      <div class="block-title">
        <h3>${title}</h3>
        <span class="muted">0 из ${requests.length} шт.</span>
      </div>
      ${renderPaymentFilters()}
      <div class="empty-state">По выбранным фильтрам заявок нет.</div>
    `;
  }

  return `
    <div class="block-title">
      <h3>${title}</h3>
      <span class="muted">${filteredRequests.length} из ${requests.length} шт.</span>
    </div>
    ${renderPaymentFilters()}
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
              <td>${request.manager_name || ""}</td>
              <td><strong>${request.client_name || request.event_title || request.event_id || ""}</strong></td>
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
      await loadDashboard();
    });
  }

  const paymentSearch = document.getElementById("paymentSearch");
  if (paymentSearch) {
    paymentSearch.addEventListener("input", (event) => {
      state.paymentSearch = event.target.value;
      clearTimeout(window.__cfPaymentSearchTimer);
      window.__cfPaymentSearchTimer = setTimeout(() => {
        loadDashboard().catch((error) => alert(error.message));
      }, 350);
    });
  }

  const eventDepartment = document.getElementById("eventDepartmentFilter");
  if (eventDepartment) {
    eventDepartment.addEventListener("change", async (event) => {
      state.eventDepartmentFilter = event.target.value;
      await loadDashboard();
    });
  }

  const eventManager = document.getElementById("eventManagerFilter");
  if (eventManager) {
    eventManager.addEventListener("change", async (event) => {
      state.eventManagerFilter = event.target.value;
      await loadDashboard();
    });
  }

  const eventStatus = document.getElementById("eventStatusFilter");
  if (eventStatus) {
    eventStatus.addEventListener("change", async (event) => {
      state.eventStatusFilter = event.target.value;
      await loadDashboard();
    });
  }

  const eventSearch = document.getElementById("eventSearch");
  if (eventSearch) {
    eventSearch.addEventListener("input", (event) => {
      state.eventSearch = event.target.value;
      clearTimeout(window.__cfEventSearchTimer);
      window.__cfEventSearchTimer = setTimeout(() => {
        loadDashboard().catch((error) => alert(error.message));
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
        await loadDashboard();
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
        await loadDashboard();
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

    $("eventModalContent").innerHTML = `
      <div class="grid cards">
        ${metric("Оборот", formatMoney(summary.external_total))}
        ${metric("Факт", formatMoney(summary.fact_total))}
        ${metric("Оплачено", formatMoney(summary.paid_total))}
        ${metric("Доход компании", formatMoney(summary.final_company_income))}
      </div>

      <div class="divider"></div>

      <h3>Смета</h3>
      <div class="table-wrap estimate-table-wrap">
        <table class="estimate-table">
          <thead>
            <tr>
              <th>Позиция</th><th>Тип</th><th>Смета</th><th>Факт</th><th>Оплата</th><th>Способ</th><th>НДС</th><th>Вычеты</th>
            </tr>
          </thead>
          <tbody>
            ${(items || []).map((item) => `
              <tr>
                <td><strong>${item.external_name}</strong></td>
                <td>${item.item_type}</td>
                <td>${formatMoney(item.external_amount)}</td>
                <td>${formatMoney(item.amount_fact)}</td>
                <td>${formatMoney(item.paid_amount)}</td>
                <td>${paymentMethodLabel(item.payment_method)}</td>
                <td>${formatMoney(item.vat_amount)}</td>
                <td>${formatMoney(item.deduction_amount)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>

      ${renderPaymentRequestsTable(requests || [], "Заявки мероприятия")}
    `;

    attachPaymentRequestActions();
    attachFilters();
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

  renderSummary([
    ["План компании", formatMoney(data.company_plan_amount)],
    ["Факт компании", formatMoney(data.company_fact_income_amount)],
    ["Выполнение", `${data.company_completion_percent}%`],
    ["Расходы", formatMoney(data.company_expenses_amount)],
  ]);

  $("dashboardTitle").textContent = "Админка";
  $("dashboardHint").textContent = "Скелет вкладок v0.30";

  if (state.activeAdminTab === "overview") {
    $("dashboardContent").innerHTML = renderAdminOverview(data);
  } else if (state.activeAdminTab === "events") {
    $("dashboardContent").innerHTML = renderAdminEvents(data);
  } else if (state.activeAdminTab === "requests") {
    $("dashboardContent").innerHTML = renderPaymentRequestsTable(data.payment_requests || [], "Все заявки");
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

function renderManagerDashboard(data, paymentRequests = []) {
  $("adminTabs").classList.add("hidden");
  renderSummary([
    ["Личный план", formatMoney(data.personal_plan_amount)],
    ["Факт", formatMoney(data.fact_income_amount)],
    ["Выполнение", `${data.completion_percent}%`],
    ["Остаток", formatMoney(data.remaining_to_plan)],
  ]);

  $("dashboardTitle").textContent = `Кабинет менеджера: ${data.manager_name}`;
  $("dashboardHint").textContent = data.department_name || "";

  $("dashboardContent").innerHTML = `
    <div class="grid cards">
      ${metric("Мероприятий", data.events_count)}
      ${metric("Черновиков", data.drafts_count)}
      ${metric("Заявок", data.payment_requests_count)}
      ${metric("Активных заявок", data.active_payment_requests_count)}
    </div>
    <div class="block-title"><h3>Мероприятия</h3></div>
    ${renderEventsTable(data.events || [], true)}
    ${renderPaymentRequestsTable(paymentRequests, "Мои заявки")}
  `;

  attachPaymentRequestActions();
  attachFilters();
  attachEventRows();
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
  const month = $("monthInput").value || state.month;
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
      : "Финансовая панель мероприятий";
    $("userBadge").textContent = `${user.name} · ${roleLabel(user.role)}`;
    $("monthInput").value = state.month;

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
  loadDashboard().catch((error) => alert(error.message));
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
