(() => {
  const MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    "январь": 1, "февраль": 2, "март": 3, "апрель": 4, "май": 5, "июнь": 6,
    "июль": 7, "август": 8, "сентябрь": 9, "октябрь": 10, "ноябрь": 11, "декабрь": 12,
    "қаңтар": 1, "ақпан": 2, "наурыз": 3, "сәуір": 4, "мамыр": 5, "маусым": 6,
    "шілде": 7, "тамыз": 8, "қыркүйек": 9, "қазан": 10, "қараша": 11, "желтоқсан": 12,
  };
  const MONTH_PATTERN = Object.keys(MONTHS)
    .sort((a, b) => b.length - a.length)
    .map((value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
    .join("|");

  function isoLocal(year, month, day, hour = 0, minute = 0, second = 0) {
    const d = new Date(year, month - 1, day, hour, minute, second, 0);
    if (Number.isNaN(d.getTime())) return null;
    if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) return null;
    const pad = (v) => String(v).padStart(2, "0");
    return `${year}-${pad(month)}-${pad(day)}T${pad(hour)}:${pad(minute)}:${pad(second)}`;
  }

  function parseReceiptDateV105(text) {
    const source = String(text || "").replace(/\u00a0/g, " ");
    let m = source.match(new RegExp(`(?:^|\\D)(\\d{1,2})\\s+(${MONTH_PATTERN})\\s+(20\\d{2})(?:\\s*(?:г(?:ода)?|ж(?:ылы)?|жылғы)?\\.?\\s*)?(?:[,;\\s]+(?:в\\s*)?(\\d{1,2})[:.](\\d{2})(?::(\\d{2}))?)?`, "i"));
    if (m) return isoLocal(Number(m[3]), MONTHS[m[2].toLowerCase()], Number(m[1]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));

    m = source.match(new RegExp(`(?:^|\\D)(20\\d{2})\\s*(?:жылғы|ж\\.?|г\\.?|года)?\\s*(\\d{1,2})\\s+(${MONTH_PATTERN})(?:[,;\\s]+(\\d{1,2})[:.](\\d{2})(?::(\\d{2}))?)?`, "i"));
    if (m) return isoLocal(Number(m[1]), MONTHS[m[3].toLowerCase()], Number(m[2]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));

    m = source.match(/(?:^|\D)(\d{1,2})[.\/-](\d{1,2})[.\/-](20\d{2})(?:[T,;\s]+(\d{1,2})[:.](\d{2})(?::(\d{2}))?)?/);
    if (m) return isoLocal(Number(m[3]), Number(m[2]), Number(m[1]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));

    m = source.match(/(?:^|\D)(20\d{2})[-\/.](\d{1,2})[-\/.](\d{1,2})(?:[T,;\s]+(\d{1,2}):?(\d{2})(?::?(\d{2}))?)?/);
    if (m) return isoLocal(Number(m[1]), Number(m[2]), Number(m[3]), Number(m[4] || 0), Number(m[5] || 0), Number(m[6] || 0));
    return null;
  }

  function unicodeLetterCount(text) {
    return (String(text || "").match(/\p{L}/gu) || []).length;
  }

  function trimPersonCandidate(text) {
    let value = String(text || "").replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
    value = value.replace(/^[^\p{L}]+/u, "").replace(/[^\p{L}.'’\- ]+$/u, "").trim();
    return value;
  }

  function looksLikePersonName(text) {
    const clean = trimPersonCandidate(text);
    if (!clean || /\d/u.test(clean)) return false;
    const lower = clean.toLowerCase();
    if (/(?:режим|налогооблож|самозанят|бин|чек|receipt|итого|плат[её]ж|наличн|безналичн|банк|кбе|иик|contrast event|қорытынды|төлем)/iu.test(lower)) return false;
    const words = clean.split(/\s+/u).filter(Boolean);
    return words.length >= 2 && words.length <= 6 && unicodeLetterCount(clean) >= 6;
  }

  function extractUnicodeName(text) {
    const lines = String(text || "").replace(/\u00a0/g, " ").replace(/\r/g, "")
      .split("\n").map((line) => line.replace(/\s+/g, " ").trim()).filter(Boolean);
    const iinIndex = lines.findIndex((line) => /(?:ИИН|IIN|ЖСН)/iu.test(line));
    if (iinIndex < 0) return null;
    const indexes = [];
    for (let i = iinIndex + 1; i <= Math.min(lines.length - 1, iinIndex + 5); i += 1) indexes.push(i);
    for (let i = iinIndex - 1; i >= Math.max(0, iinIndex - 4); i -= 1) indexes.push(i);
    for (const index of indexes) {
      const candidate = trimPersonCandidate(lines[index]);
      if (looksLikePersonName(candidate)) return candidate;
    }
    return null;
  }

  window.accountingParseReceiptDate = parseReceiptDateV105;

  const previousParser = window.accountingParseESalyqText;
  if (typeof previousParser === "function") {
    window.accountingParseESalyqText = (rawText, requestAmount = null) => {
      const result = previousParser(rawText, requestAmount) || {};
      const receiptDate = parseReceiptDateV105(rawText);
      if (receiptDate) result.receipt_datetime = receiptDate;
      const exactName = extractUnicodeName(rawText);
      if (exactName) result.contractor_full_name = exactName;
      return result;
    };
  }

  // Tesseract is only a reserve when QR/KGD cannot provide the receipt. If that
  // reserve is needed, load the Kazakh model too. Fall back to the old rus+eng
  // model if the CDN cannot provide kaz.traineddata.
  function patchTesseract(instance) {
    if (!instance || typeof instance.recognize !== "function" || instance.__contrastKazakhPatched) return instance;
    const originalRecognize = instance.recognize.bind(instance);
    instance.recognize = async (image, languages, options) => {
      if (String(languages || "") === "rus+eng") {
        try {
          return await originalRecognize(image, "kaz+rus+eng", options);
        } catch (error) {
          console.warn("Kazakh OCR model unavailable, falling back to rus+eng", error);
          return originalRecognize(image, "rus+eng", options);
        }
      }
      return originalRecognize(image, languages, options);
    };
    instance.__contrastKazakhPatched = true;
    return instance;
  }

  let tesseractValue = patchTesseract(window.Tesseract);
  try {
    const descriptor = Object.getOwnPropertyDescriptor(window, "Tesseract");
    if (!descriptor || descriptor.configurable) {
      Object.defineProperty(window, "Tesseract", {
        configurable: true,
        enumerable: true,
        get() { return tesseractValue; },
        set(value) { tesseractValue = patchTesseract(value); },
      });
    } else if (window.Tesseract) {
      patchTesseract(window.Tesseract);
    }
  } catch (_) {
    if (window.Tesseract) patchTesseract(window.Tesseract);
  }

  const previousDisplayDate = window.accountingDisplayDate;
  if (typeof previousDisplayDate === "function") {
    window.accountingDisplayDate = (row) => {
      if (row?.has_receipt && !row?.receipt_datetime) return "Дата не распознана";
      return previousDisplayDate(row);
    };
  }

  console.info("Contrast Finance accounting receipt date/Kazakh fix v0.5.105 loaded");
})();
