(() => {
  const RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
  };

  function isoLocal(year, month, day, hour = 0, minute = 0, second = 0) {
    const d = new Date(year, month - 1, day, hour, minute, second, 0);
    if (Number.isNaN(d.getTime())) return null;
    if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) return null;
    const pad = (v) => String(v).padStart(2, "0");
    return `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}:${pad(second)}`;
  }

  function parseReceiptDateV104(text) {
    const source = String(text || "");
    let m = source.match(/(?:^|\D)(\d{1,2})\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+(20\d{2})(?:\s*г(?:ода)?\.?\s*)?(?:[,;\s]+(?:в\s*)?(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?/i);
    if (m) return isoLocal(Number(m[3]), RU_MONTHS[m[2].toLowerCase()], Number(m[1]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));

    m = source.match(/(?:^|\D)(\d{1,2})[.\/-](\d{1,2})[.\/-](20\d{2})(?:[T,;\s]+(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?/);
    if (m) return isoLocal(Number(m[3]), Number(m[2]), Number(m[1]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));

    m = source.match(/(?:^|\D)(20\d{2})-(\d{1,2})-(\d{1,2})(?:[T,;\s]+(\d{1,2}):(\d{2})(?::(\d{2}))?)?/);
    if (m) return isoLocal(Number(m[1]), Number(m[2]), Number(m[3]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));
    return null;
  }

  // Classic script globals from app.js are mutable through window.
  window.accountingParseReceiptDate = parseReceiptDateV104;

  const previousDisplayDate = window.accountingDisplayDate;
  if (typeof previousDisplayDate === "function") {
    window.accountingDisplayDate = (row) => {
      if (row?.has_receipt && !row?.receipt_datetime) return "Дата не распознана";
      return previousDisplayDate(row);
    };
  }

  console.info("Contrast Finance accounting receipt date fix v0.5.104 loaded");
})();
