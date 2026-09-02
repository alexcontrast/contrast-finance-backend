"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("app/web/app.js", "utf8");
const start = source.indexOf("const ACCOUNTING_RU_MONTHS");
const end = source.indexOf("function accountingParseESalyqText", start);
assert.ok(start >= 0 && end > start, "accounting date parser block not found");

const context = {};
vm.runInNewContext(
  `${source.slice(start, end)}\nglobalThis.parseReceiptDate = accountingParseReceiptDate;`,
  context,
);

assert.equal(
  context.parseReceiptDate("Чек №000000000011 от 4 мая 2O26 г., 12.08"),
  "2026-05-04T12:08:00",
);
assert.equal(
  context.parseReceiptDate("Дата и время по Астане O1.O9.2O26 12:52"),
  "2026-09-01T12:52:00",
);
assert.equal(
  context.parseReceiptDate("2026 жылғы 28 тамыз, 13:36"),
  "2026-08-28T13:36:00",
);
assert.equal(
  context.parseReceiptDate("oT 3 aprycta 2026 r., 12:07"),
  "2026-08-03T12:07:00",
);
assert.equal(
  context.parseReceiptDate("oT 3 aBrycta 2026 r., 15:06"),
  "2026-08-03T15:06:00",
);

console.log("browser receipt date parser: 5/5 passed");
