"""Fixed customer requisites for future R-1 act generation.

These values describe the customer side of the primary accounting document and
are intentionally kept in one backend location so receipt OCR never tries to
infer them from e-Salyq screenshots.
"""

R1_CUSTOMER_PROFILE = {
    "name": 'ИП "Contrast Event"',
    "bin_iin": "881118350706",
    "country": "КАЗАХСТАН",
    "address": "город АСТАНА, БАЙКОНЫРСКИЙ РАЙОН, МИКРОРАЙОН Целинный, УЛИЦА Александра Кравцова, дом 7/1, квартира 32",
    "iik": "KZ676017111000029431",
    "bank_name": 'АО «Народный Банк Казахстана»',
    "bik": "HSBKKZKX",
    "kbe": "19",
    "director": "Трубицкий А. А.",
}
