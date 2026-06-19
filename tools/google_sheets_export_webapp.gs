/**
 * Contrast Finance 2.0 → Google Sheets archive receiver.
 *
 * Deploy this file inside the archive Google spreadsheet:
 * Apps Script → Deploy → New deployment → Web app.
 * Execute as: Me. Access: Anyone with the link.
 * Put the Web App URL into Railway secret GOOGLE_SHEETS_EXPORT_WEBHOOK_URL.
 * Optional security token: set Script Property GOOGLE_SHEETS_EXPORT_TOKEN
 * and the same value in Railway secret GOOGLE_SHEETS_EXPORT_TOKEN.
 */
function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents || '{}');
    var expectedToken = PropertiesService.getScriptProperties().getProperty('GOOGLE_SHEETS_EXPORT_TOKEN');
    if (expectedToken && payload.token !== expectedToken) {
      return jsonResponse({ ok: false, message: 'Bad token' }, 403);
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
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

function getOrCreateSheet_(ss, name) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  sheet.clear({ contentsOnly: false });
  return sheet;
}

function money_(value) {
  return Number(value || 0);
}

function renderMonthlySheet_(ss, monthly, title) {
  var sheet = getOrCreateSheet_(ss, monthly.sheet_name || title);
  sheet.setFrozenRows(4);
  sheet.setHiddenGridlines(true);

  var summary = monthly.summary || {};
  sheet.getRange('A1:J1').merge().setValue('Сводка месяца — ' + (title || monthly.sheet_name || ''));
  sheet.getRange('A1').setFontSize(18).setFontWeight('bold').setBackground('#e7ffd9');
  sheet.getRange('A2').setValue('Оборот');
  sheet.getRange('B2').setValue(money_(summary.turnover));
  sheet.getRange('C2').setValue('План');
  sheet.getRange('D2').setValue(money_(summary.plan));
  sheet.getRange('E2').setValue('НДС к уплате');
  sheet.getRange('F2').setValue(money_(summary.vat_to_pay));
  sheet.getRange('G2').setValue('Налоги к уплате');
  sheet.getRange('H2').setValue(money_(summary.tax_to_pay));
  sheet.getRange('I2').setValue('Расходы');
  sheet.getRange('J2').setValue(money_(summary.expenses));
  sheet.getRange('A2:J2').setFontWeight('bold').setBackground('#f3ffe9');
  sheet.getRange('B2:D2').setNumberFormat('#,##0');
  sheet.getRange('F2:J2').setNumberFormat('#,##0');

  var row = 4;
  var events = monthly.events || [];
  events.forEach(function(ev) {
    sheet.getRange(row, 1, 1, 10).merge().setValue(
      (ev.date || '') + ' · ' + (ev.client || '') + ' · ' + (ev.title || '') + ' · ' + (ev.manager || '')
    );
    sheet.getRange(row, 1).setFontWeight('bold').setBackground('#fff2cc');
    row++;

    var info = [
      ['Статус', ev.status || '', 'Деньги', ev.money_status || '', 'Тип расчёта', ev.client_calc_type || '', 'Оборот', money_(ev.summary && ev.summary.turnover), 'Доход', money_(ev.summary && ev.summary.final_company_income)]
    ];
    sheet.getRange(row, 1, 1, 10).setValues(info).setBackground('#f8fbf5');
    sheet.getRange(row, 8, 1, 3).setNumberFormat('#,##0');
    row++;

    var headers = [['Позиция', 'Смета', 'Факт', 'Оплачено', 'Остаток', 'НДС', 'Вычеты', 'Способ', 'БИН/ИИН', 'Комментарий']];
    sheet.getRange(row, 1, 1, 10).setValues(headers).setFontWeight('bold').setBackground('#eef5e8');
    row++;

    var items = ev.items || [];
    if (!items.length) {
      sheet.getRange(row, 1, 1, 10).merge().setValue('Позиций нет').setFontColor('#777777');
      row++;
    } else {
      var values = items.map(function(item) {
        return [
          item.name || '',
          money_(item.external_amount),
          money_(item.fact_amount),
          money_(item.paid_amount),
          money_(item.fact_amount) - money_(item.paid_amount),
          money_(item.vat_amount),
          money_(item.deduction_amount),
          item.payment_method || '',
          item.iin_bin || '',
          item.note || ''
        ];
      });
      sheet.getRange(row, 1, values.length, 10).setValues(values);
      sheet.getRange(row, 2, values.length, 6).setNumberFormat('#,##0');
      row += values.length;
    }

    var totalRow = [['Итого', money_(ev.summary && ev.summary.external_total), money_(ev.summary && ev.summary.fact_total), money_(ev.summary && ev.summary.paid_total), '', money_(ev.summary && ev.summary.vat_to_pay), money_(ev.summary && ev.summary.deductions_total), '', '', '']];
    sheet.getRange(row, 1, 1, 10).setValues(totalRow).setFontWeight('bold').setBackground('#e7ffd9');
    sheet.getRange(row, 2, 1, 6).setNumberFormat('#,##0');
    row += 2;
  });

  sheet.setColumnWidths(1, 1, 240);
  sheet.setColumnWidths(2, 6, 95);
  sheet.setColumnWidths(8, 1, 110);
  sheet.setColumnWidths(9, 1, 120);
  sheet.setColumnWidths(10, 1, 220);
  sheet.getRange(1, 1, Math.max(row, 4), 10).setFontFamily('Arial').setVerticalAlignment('middle');
}

function renderPaymentRequestsSheet_(ss, requestsSheet) {
  var sheet = getOrCreateSheet_(ss, requestsSheet.sheet_name || 'Заявки на оплату');
  sheet.setFrozenRows(2);
  sheet.setHiddenGridlines(true);
  sheet.getRange('A1:K1').merge().setValue('Заявки на оплату');
  sheet.getRange('A1').setFontSize(18).setFontWeight('bold').setBackground('#e7ffd9');

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
    sheet.getRange(3, 7, rows.length, 1).setNumberFormat('#,##0');
  }

  var lastRow = Math.max(3, rows.length + 2);
  sheet.getRange(1, 1, lastRow, headers[0].length).setFontFamily('Arial').setVerticalAlignment('middle');
  sheet.setColumnWidths(1, 2, 105);
  sheet.setColumnWidths(3, 1, 150);
  sheet.setColumnWidths(4, 3, 180);
  sheet.setColumnWidths(7, 1, 110);
  sheet.setColumnWidths(8, 3, 120);
  sheet.setColumnWidths(11, 1, 240);

  for (var r = 3; r <= lastRow; r++) {
    var bg = r % 2 === 0 ? '#ffffff' : '#f8fbf5';
    sheet.getRange(r, 1, 1, headers[0].length).setBackground(bg);
  }
}
