/**
 * Contrast Finance 2.0 → Google Sheets archive receiver.
 * v0.5.9: VAT deductions are shown in VAT column and also added to Commission column as company income.
 *         Keeps agency commission row above VAT, manager percent label, money grouping and tax gross/net logic.
 * Deploy inside the archive Google spreadsheet as Web App.
 */
function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents || '{}');
    var expectedToken = PropertiesService.getScriptProperties().getProperty('GOOGLE_SHEETS_EXPORT_TOKEN');
    if (expectedToken && payload.token !== expectedToken) {
      return jsonResponse({ ok: false, message: 'Bad token' }, 403);
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    applyArchiveLocale_(ss);
    cleanupTechnicalSheets_(ss);
    var updated = [];

    if (payload.sheets && payload.sheets.monthly) {
      renderMonthlySheet_(ss, payload.sheets.monthly, payload.month_title || payload.month);
      updated.push(payload.sheets.monthly.sheet_name);
    }
    if (payload.sheets && payload.sheets.payment_requests) {
      renderPaymentRequestsSheet_(ss, payload.sheets.payment_requests);
      updated.push(payload.sheets.payment_requests.sheet_name);
    }

    return jsonResponse({
      ok: true,
      message: 'Архив обновлён',
      spreadsheet_url: ss.getUrl(),
      updated_sheets: updated
    });
  } catch (err) {
    return jsonResponse({ ok: false, message: String(err), stack: String(err && err.stack || '') }, 500);
  }
}

function jsonResponse(obj, statusCode) {
  var output = ContentService.createTextOutput(JSON.stringify(obj));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

function applyArchiveLocale_(ss) {
  // Number grouping in Google Sheets is locale-dependent. Kazakhstan/Russian locale
  // gives spaces in all groups: 1 000 000, not 1000 000.
  try {
    var current = String(ss.getSpreadsheetLocale && ss.getSpreadsheetLocale() || '').toLowerCase();
    if (current.indexOf('ru') !== 0 && current.indexOf('kk') !== 0) {
      try {
        ss.setSpreadsheetLocale('ru_KZ');
      } catch (errKz) {
        ss.setSpreadsheetLocale('ru');
      }
    }
  } catch (err) {
    // Formatting below still works; this just protects against locale permission/code issues.
  }
}

function getOrCreateSheet_(ss, name) {
  // Strong reset: delete the old archive sheet and recreate it from zero.
  // This is safer than clear()+breakApart() because old Google Sheets files may
  // contain merged/protected/partially formatted ranges outside getDataRange().
  // Those stale ranges caused partial redraws and "merge/break apart selected range" errors.
  var existing = ss.getSheetByName(name);
  var targetIndex = existing ? Math.max(0, existing.getIndex() - 1) : ss.getSheets().length;
  var tempName = '__contrast_export_temp__';
  var temp = null;

  if (existing) {
    if (ss.getSheets().length <= 1) {
      temp = ss.insertSheet(tempName);
    }
    ss.deleteSheet(existing);
  }

  var sheet = ss.insertSheet(name, Math.min(targetIndex, ss.getSheets().length));
  resetSheet_(sheet);

  if (temp) {
    ss.deleteSheet(temp);
  }
  return sheet;
}

function resetSheet_(sheet) {
  // Keep this helper for newly created sheets and future safety.
  var merged = sheet.getDataRange().getMergedRanges();
  merged.forEach(function(range) {
    range.breakApart();
  });
  sheet.clear({ contentsOnly: false });
  sheet.clearConditionalFormatRules();
  sheet.setFrozenRows(0);
  sheet.setFrozenColumns(0);
  if (sheet.getFilter()) sheet.getFilter().remove();
}

function cleanupTechnicalSheets_(ss) {
  var keepMonthly = /^(Январь|Февраль|Март|Апрель|Май|Июнь|Июль|Август|Сентябрь|Октябрь|Ноябрь|Декабрь)\s+\d{4}$/;
  var keep = { 'Заявки на оплату': true };
  var technical = {
    'Лист1': true,
    '_MIGRATION_EXPORT_JSON': true,
    'Реестр_ивентов': true,
    'Позиции_ивентов': true,
    'Заявки_на_оплату': true,
    'Оплаты_заказчиков': true,
    'Черновики_ивентов': true,
    'Пользователи': true,
    'Цели': true,
    'Справочники': true
  };
  var sheets = ss.getSheets();
  if (sheets.length <= 1) return;
  sheets.forEach(function(sheet) {
    var name = sheet.getName();
    if (technical[name] && ss.getSheets().length > 1 && !keep[name] && !keepMonthly.test(name)) {
      ss.deleteSheet(sheet);
    }
  });
}

function money_(value) {
  return Number(value || 0);
}

function hasValue_(obj, key) {
  return obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== '';
}

function firstNumber_(obj, keys, fallback) {
  for (var i = 0; i < keys.length; i++) {
    if (hasValue_(obj, keys[i])) return money_(obj[keys[i]]);
  }
  return fallback === undefined ? 0 : money_(fallback);
}


function firstNumberOrNull_(obj, keys) {
  for (var i = 0; i < keys.length; i++) {
    if (hasValue_(obj, keys[i])) return money_(obj[keys[i]]);
  }
  return null;
}

function sumItemsExternal_(items) {
  var total = 0;
  (items || []).forEach(function(item) {
    total += money_(item.external_amount);
  });
  return total;
}

function firstValue_(obj, keys, fallback) {
  for (var i = 0; i < keys.length; i++) {
    if (hasValue_(obj, keys[i])) return obj[keys[i]];
  }
  return fallback;
}

function formatPercentLabel_(value, fallback) {
  var raw = value;
  if (raw === undefined || raw === null || raw === '') raw = fallback;
  if (raw === undefined || raw === null || raw === '') return '';
  var n = Number(String(raw).replace(',', '.'));
  if (!isFinite(n)) return String(raw);
  if (Math.abs(n) > 0 && Math.abs(n) <= 1) n = n * 100;
  var rounded = Math.round(n * 100) / 100;
  if (Math.abs(rounded - Math.round(rounded)) < 0.000001) return String(Math.round(rounded)) + '%';
  return String(rounded).replace('.', ',') + '%';
}

function labelWithPercent_(label, percentValue, fallbackPercent) {
  var suffix = formatPercentLabel_(percentValue, fallbackPercent);
  return suffix ? label + ' ' + suffix : label;
}

function formatMoneyRange_(range) {
  // Keep values numeric, but use grouped display. With archive locale ru/kk this renders as:
  // 1 000, 1 000 000, -1 000 000.
  range.setNumberFormat('#,##0');
}

function setBorder_(range) {
  range.setBorder(true, true, true, true, true, true, '#000000', SpreadsheetApp.BorderStyle.SOLID);
}

function statusFill_(status) {
  if (status === 'Принято' || status === 'Оплачено' || status === 'Деньги в кассе') return '#d9ead3';
  if (status === 'На проверке' || status === 'Новая' || status === 'На оплату') return '#fff2cc';
  if (status === 'Отменено' || status === 'На доработке') return '#f4cccc';
  return '#ffffff';
}

function renderMonthlySheet_(ss, monthly, title) {
  var sheet = getOrCreateSheet_(ss, monthly.sheet_name || title);
  sheet.setFrozenRows(0);
  sheet.setHiddenGridlines(false);
  var maxRows = Math.max(sheet.getMaxRows(), 1200);
  if (sheet.getMaxRows() < maxRows) sheet.insertRowsAfter(sheet.getMaxRows(), maxRows - sheet.getMaxRows());

  var summary = monthly.summary || {};
  var plan = money_(summary.plan);
  var income = money_(summary.company_income);
  var remaining = plan - income;

  sheet.getRange('A1:B1').merge().setValue('Сводка месяца');
  sheet.getRange('A1:B1').setFontSize(13).setFontWeight('bold').setHorizontalAlignment('center').setBackground('#bfbfbf');
  setBorder_(sheet.getRange('A1:B8'));

  var summaryValues = [
    ['Кол-во мероприятий', money_(summary.events_count)],
    ['Оборот', money_(summary.turnover)],
    ['Налоги', money_(summary.tax_to_pay)],
    ['НДС', money_(summary.vat_to_pay)],
    ['Общий доход компании', income],
    ['Цель', plan],
    ['Остаток до цели', remaining]
  ];
  sheet.getRange(2, 1, summaryValues.length, 2).setValues(summaryValues);
  sheet.getRange('A2:A5').setFontWeight('bold').setBackground('#f4cccc');
  sheet.getRange('A6:B6').setFontWeight('bold').setBackground('#d9ead3');
  sheet.getRange('A7:A7').setFontWeight('bold').setBackground('#f4cccc');
  sheet.getRange('A8:B8').setFontWeight('bold').setFontSize(14).setBackground('#ffff00');
  formatMoneyRange_(sheet.getRange('B2:B8'));
  sheet.getRange('B2:B8').setHorizontalAlignment('right');

  var row = 11;
  var events = monthly.events || [];
  events.forEach(function(ev) {
    var s = ev.summary || {};
    var items = ev.items || [];

    // Event title row: client + date + title, matching old archive style.
    sheet.getRange(row, 1).setValue(ev.client || '');
    sheet.getRange(row, 2).setValue(ev.date || '').setNumberFormat('dd.mm.yyyy');
    sheet.getRange(row, 3, 1, 5).merge().setValue(ev.title || '');
    sheet.getRange(row, 1, 1, 2).setBackground('#ffff00').setFontWeight('bold').setHorizontalAlignment('center');
    sheet.getRange(row, 3, 1, 5).setBackground('#ffffff').setFontWeight('bold').setHorizontalAlignment('left');
    setBorder_(sheet.getRange(row, 1, 1, 7));
    row++;

    // Header row: manager in first cell, then column headers.
    var headers = [[ev.manager || '', 'Стоимость', 'Расход', 'НДС', 'Вычеты', 'Комиссия', 'Оплачено']];
    sheet.getRange(row, 1, 1, 7).setValues(headers).setFontWeight('bold');
    sheet.getRange(row, 1).setBackground('#ffffff');
    sheet.getRange(row, 2).setBackground('#ffffff');
    sheet.getRange(row, 3).setBackground('#d9d9d9');
    sheet.getRange(row, 4).setBackground('#daeef3');
    sheet.getRange(row, 5).setBackground('#e5dfec');
    sheet.getRange(row, 6).setBackground('#dbe5f1');
    sheet.getRange(row, 7).setBackground('#ffffff');
    setBorder_(sheet.getRange(row, 1, 1, 7));
    row++;

    var startItemsRow = row;
    var values = [];
    items.forEach(function(item) {
      var externalAmount = money_(item.external_amount);
      var factAmount = money_(item.fact_amount);
      values.push([
        item.name || '',
        externalAmount,
        factAmount,
        money_(item.vat_amount),
        money_(item.deduction_amount),
        externalAmount - factAmount,
        money_(item.paid_amount)
      ]);
    });

    // Old-style special calculation rows.
    // Комиссия агентства must be visible in every event table and placed
    // directly above VAT. Prefer explicit backend amount; if it is not present
    // yet, rebuild it from total payable - positions total - client VAT.
    var agencyAmountKeys = [
      'agencyAmount',
      'agency_amount',
      'agency_commission',
      'agency_commission_amount',
      'agency_fee',
      'agency_fee_amount',
      'service_fee',
      'service_fee_amount',
      'customer_commission',
      'customer_commission_amount'
    ];
    var agencyCommissionDirect = firstNumberOrNull_(s, agencyAmountKeys);
    var agencyCommission = agencyCommissionDirect !== null
      ? agencyCommissionDirect
      : money_(s.external_total) - sumItemsExternal_(items) - money_(s.client_vat);
    if (Math.abs(agencyCommission) < 0.000001) agencyCommission = 0;

    var agencyPercentKeys = [
      'agencyPercent',
      'agency_percent',
      'agency_commission_percent',
      'agency_fee_percent',
      'agency_rate',
      'agency_commission_rate',
      'service_fee_percent',
      'customer_commission_percent',
      'commission_percent',
      'markup_percent',
      'customer_markup_percent'
    ];
    var agencyPercent = firstValue_(s, agencyPercentKeys, firstValue_(ev, agencyPercentKeys, ''));
    values.push([labelWithPercent_('Комиссия агентства', agencyPercent, ''), agencyCommission, '', '', '', agencyCommission, '']);

    // НДС:
    //   Стоимость = НДС, выставленный заказчику по смете;
    //   Расход/Факт = пусто;
    //   НДС = вся сумма НДС-вычетов от подрядчиков;
    //   Комиссия = та же сумма НДС-вычетов как доход компании;
    //   Вычеты/Оплачено = пусто.
    var vatCredit = money_(s.contractor_vat_credit);
    values.push(['НДС', money_(s.client_vat), '', vatCredit, '', vatCredit, '']);

    // Налоги:
    //   Расход/Факт = первичная сумма налоговых расходов ДО вычетов;
    //   Вычеты = сумма всех налоговых вычетов;
    //   Комиссия = реальный минус по налогам: -(Факт - Вычеты).
    // If backend does not send taxes_total yet, rebuild gross tax from net tax_to_pay + deductions.
    var taxDeductions = money_(s.deductions_total);
    var taxGross = hasValue_(s, 'taxes_total') ? money_(s.taxes_total) : money_(s.tax_to_pay) + taxDeductions;
    var taxNet = taxGross - taxDeductions;
    values.push(['Налоги', '', taxGross, 0, taxDeductions, taxNet * -1, '']);

    var managerPercent = firstValue_(s, [
      'manager_percent',
      'manager_salary_percent',
      'manager_rate',
      'manager_salary_rate',
      'salary_percent'
    ], 21);
    values.push([labelWithPercent_('Менеджер', managerPercent, 21), '', '', '', '', money_(s.manager_salary) * -1, '']);

    if (values.length) {
      sheet.getRange(row, 1, values.length, 7).setValues(values);
      formatMoneyRange_(sheet.getRange(row, 2, values.length, 6));
      setBorder_(sheet.getRange(row, 1, values.length, 7));
      sheet.getRange(row, 3, values.length, 1).setBackground('#d9d9d9');
      sheet.getRange(row, 4, values.length, 1).setBackground('#daeef3');
      sheet.getRange(row, 5, values.length, 1).setBackground('#e5dfec');
      sheet.getRange(row, 6, values.length, 1).setBackground('#dbe5f1');
      if (values.length > 0) sheet.getRange(startItemsRow, 1, 1, 7).setBackground('#e2f0d9');
      row += values.length;
    }

    // Total row: Fact/Rashod column is intentionally blank.
    var totalRow = [['Итого:', money_(s.external_total), '', '', '', money_(s.final_company_income), ev.status || '']];
    sheet.getRange(row, 1, 1, 7).setValues(totalRow).setFontWeight('bold').setBackground('#fce4d6');
    sheet.getRange(row, 7).setBackground(statusFill_(ev.status)).setHorizontalAlignment('center');
    formatMoneyRange_(sheet.getRange(row, 2, 1, 5));
    setBorder_(sheet.getRange(row, 1, 1, 7));
    row += 2;
  });

  sheet.setColumnWidth(1, 260);
  sheet.setColumnWidth(2, 140);
  sheet.setColumnWidth(3, 120);
  sheet.setColumnWidth(4, 100);
  sheet.setColumnWidth(5, 110);
  sheet.setColumnWidth(6, 130);
  sheet.setColumnWidth(7, 130);
  sheet.getRange(1, 1, Math.max(row, 20), 7).setFontFamily('Arial').setFontSize(10).setVerticalAlignment('middle');
  sheet.getRange(1, 1, Math.max(row, 20), 7).setWrap(false);
  sheet.autoResizeRows(1, Math.min(row, 500));
}

function renderPaymentRequestsSheet_(ss, requestsSheet) {
  var sheet = getOrCreateSheet_(ss, requestsSheet.sheet_name || 'Заявки на оплату');
  sheet.setFrozenRows(2);
  sheet.setHiddenGridlines(true);
  sheet.getRange('A1:K1').merge().setValue('Заявки на оплату');
  sheet.getRange('A1:K1').setFontSize(18).setFontWeight('bold').setBackground('#e7ffd9').setHorizontalAlignment('left');

  var headers = [['Дата', 'Создана', 'Менеджер', 'Заказчик', 'Мероприятие', 'Позиция', 'Сумма', 'Способ', 'Статус оплаты', 'Статус денег', 'Комментарий']];
  sheet.getRange(2, 1, 1, headers[0].length).setValues(headers).setFontWeight('bold').setBackground('#eef5e8');

  var rows = (requestsSheet.rows || []).map(function(row) {
    return [
      row.event_date || '',
      row.created_at || '',
      row.manager || '',
      row.client || '',
      row.event || '',
      row.position || '',
      money_(row.amount),
      row.payment_method || '',
      row.payment_status || '',
      row.money_status || '',
      row.comment || ''
    ];
  });
  if (rows.length) {
    sheet.getRange(3, 1, rows.length, headers[0].length).setValues(rows);
    formatMoneyRange_(sheet.getRange(3, 7, rows.length, 1));
  }

  var lastRow = Math.max(3, rows.length + 2);
  var all = sheet.getRange(1, 1, lastRow, headers[0].length);
  all.setFontFamily('Arial').setFontSize(10).setVerticalAlignment('middle').setWrap(false);
  sheet.getRange(2, 1, lastRow - 1, headers[0].length).setBorder(true, true, true, true, true, true, '#e4eadf', SpreadsheetApp.BorderStyle.SOLID);
  sheet.getRange(2, 1, 1, headers[0].length).setBorder(true, true, true, true, true, true, '#9ebd8d', SpreadsheetApp.BorderStyle.SOLID);
  sheet.getRange(1, 1, 1, headers[0].length).setBorder(true, true, true, true, false, false, '#4b88ff', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);

  for (var r = 3; r <= lastRow; r++) {
    var bg = r % 2 === 0 ? '#ffffff' : '#f8fbf5';
    sheet.getRange(r, 1, 1, headers[0].length).setBackground(bg);
    var payStatus = sheet.getRange(r, 9).getValue();
    var moneyStatus = sheet.getRange(r, 10).getValue();
    sheet.getRange(r, 9).setBackground(statusFill_(payStatus));
    sheet.getRange(r, 10).setBackground(statusFill_(moneyStatus));
  }

  if (sheet.getFilter()) sheet.getFilter().remove();
  sheet.getRange(2, 1, Math.max(1, lastRow - 1), headers[0].length).createFilter();
  sheet.setColumnWidth(1, 92);
  sheet.setColumnWidth(2, 130);
  sheet.setColumnWidth(3, 140);
  sheet.setColumnWidth(4, 140);
  sheet.setColumnWidth(5, 170);
  sheet.setColumnWidth(6, 230);
  sheet.setColumnWidth(7, 105);
  sheet.setColumnWidth(8, 110);
  sheet.setColumnWidth(9, 115);
  sheet.setColumnWidth(10, 125);
  sheet.setColumnWidth(11, 220);
  sheet.setRowHeights(3, Math.max(1, rows.length), 22);
}
