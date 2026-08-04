v0.5.67 changed files

app/services/google_sheets_archive_export.py

Annual admin statistics now load all required yearly datasets once and build
the same monthly aggregates in memory. Opening the statistics tab no longer
builds twelve full Google Sheets export payloads or loads payment requests.

Deploy over v0.5.66. No migration is required.
