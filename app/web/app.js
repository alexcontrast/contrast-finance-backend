const state = {
  token: localStorage.getItem("cf_token") || "",
  bootstrap: null,
  month: new Date().toISOString().slice(0, 7),
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
    rejected: "Отклонено",
  }[status] || status;
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

function renderEventsTable(events) {
  if (!events || !events.length) return `<p class="muted">Нет мероприятий за выбранный месяц.</p>`;

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
              <td>${event.event_date || ""}</td>
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

function renderDepartmentDashboard(data) {
  renderSummary([
    ["План отдела", formatMoney(data.plan_amount)],
    ["Факт", formatMoney(data.fact_income_amount)],
    ["Выполнение", `${data.completion_percent}%`],
    ["Расходы", formatMoney(data.expenses_amount)],
  ]);

  $("dashboardTitle").textContent = `Кабинет отдела: ${data.department_name}`;
  $("dashboardHint").textContent = data.include_drafts ? "С черновиками" : "Без черновиков";

  $("dashboardContent").innerHTML = `
    <div class="grid cards">
      ${metric("Остаток до плана", formatMoney(data.remaining_to_plan))}
      ${metric("Мероприятий", data.events_count)}
      ${metric("Черновиков", data.drafts_count)}
      ${metric("Менеджеров", data.managers?.length || 0)}
    </div>
    ${renderEventsTable(data.events || [])}
  `;
}

function renderManagerDashboard(data) {
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
    ${renderEventsTable(data.events || [])}
  `;
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

    <h3 style="margin-top:24px;">Мероприятия</h3>
    ${renderEventsTable(data.events || [])}
  `;
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
    renderDepartmentDashboard(await api(`/department-head-dashboard?department_id=${user.department_id}&month=${month}&include_drafts=true`));
    return;
  }

  renderManagerDashboard(await api(`/manager-dashboard?month=${month}&include_drafts=true`));
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
