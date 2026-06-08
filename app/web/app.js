const state = {
  token: localStorage.getItem("cf_token") || "",
  bootstrap: null,
  month: new Date().toISOString().slice(0, 7),
  paymentStatusFilter: "active",
  paymentSearch: "",
  eventDepartmentFilter: "all",
};

const $ = (id) => document.getElementById(id);

function formatMoney(value) {
  const n = Number(value || 0);
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n);
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
  $("pageTitle").textContent = "Вход";
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


function filteredEventsForAdmin(events) {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return events || [];

  if (state.eventDepartmentFilter === "all") return events || [];

  const depId = Number(state.eventDepartmentFilter);
  return (events || []).filter((event) => Number(event.department_id) === depId);
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
    list = list.filter((request) => {
      const client = String(request.client_name || "").toLowerCase();
      return client.includes(search);
    });
  }

  return list;
}

function renderEventDepartmentFilter(events) {
  const user = state.bootstrap?.user;
  if (!user || user.role !== "admin") return "";

  const departments = state.bootstrap?.departments || [];

  return `
    <div class="filters-row">
      <label class="compact-label">Отдел по мероприятиям
        <select id="eventDepartmentFilter">
          <option value="all">Все отделы</option>
          ${departments.map((department) => `
            <option value="${department.id}" ${String(state.eventDepartmentFilter) === String(department.id) ? "selected" : ""}>${department.name}</option>
          `).join("")}
        </select>
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
}


function renderEventsTable(events) {
  if (!events || !events.length) return `<div class="empty-state">Нет мероприятий за выбранный месяц.</div>`;

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Дата</th><th>Мероприятие</th><th>Заказчик</th><th>Статус</th>
            <th>Оборот</th><th>Доход</th><th>ЗП менеджера</th><th>Заявки</th>
          </tr>
        </thead>
        <tbody>
          ${events.map((event) => `
            <tr>
              <td class="nowrap">${event.event_date || ""}</td>
              <td><strong>${event.title || ""}</strong></td>
              <td>${event.client_name || ""}</td>
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
            <th>Заявка</th>
            <th>Заказчик</th>
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
          ${filteredRequests.map((request) => `
            <tr>
              <td>#${request.id}</td>
              <td><strong>${request.client_name || request.event_title || request.event_id || ""}</strong></td>
              <td>${request.manager_name || ""}</td>
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

function renderDepartmentDashboard(data, paymentRequests = []) {
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
    ${renderEventsTable(data.events || [])}
    ${renderPaymentRequestsTable(requests, "Заявки отдела")}
  `;

  attachPaymentRequestActions();
  attachFilters();
}

function renderManagerDashboard(data, paymentRequests = []) {
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
    ${renderEventsTable(data.events || [])}
    ${renderPaymentRequestsTable(paymentRequests, "Мои заявки")}
  `;

  attachPaymentRequestActions();
  attachFilters();
}

function renderAdminDashboard(data) {
  renderSummary([
    ["План компании", formatMoney(data.company_plan_amount)],
    ["Факт компании", formatMoney(data.company_fact_income_amount)],
    ["Выполнение", `${data.company_completion_percent}%`],
    ["Расходы", formatMoney(data.company_expenses_amount)],
  ]);

  $("dashboardTitle").textContent = "Админка";
  $("dashboardHint").textContent = "Общая картина";

  $("dashboardContent").innerHTML = `
    <h3>Отделы</h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Отдел</th><th>План</th><th>Факт</th><th>%</th><th>Расходы</th><th>Мероприятий</th></tr>
        </thead>
        <tbody>
          ${(data.departments || []).map((dep) => `
            <tr>
              <td><strong>${dep.department_name}</strong></td>
              <td>${formatMoney(dep.plan_amount)}</td>
              <td>${formatMoney(dep.fact_income_amount)}</td>
              <td>${dep.completion_percent}%</td>
              <td>${formatMoney(dep.expenses_amount)}</td>
              <td>${dep.events_count}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>

    <div class="block-title"><h3>Мероприятия</h3></div>
    ${renderEventDepartmentFilter(data.events || [])}
    ${renderEventsTable(filteredEventsForAdmin(data.events || []))}
    ${renderPaymentRequestsTable(data.payment_requests || [], "Все заявки")}
  `;

  attachPaymentRequestActions();
  attachFilters();
}

async function loadDashboard() {
  const user = state.bootstrap.user;
  const month = $("monthInput").value || state.month;
  state.month = month;

  if (user.role === "admin") {
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

boot();
