# AutoValu

AutoValu is a desktop application for evaluating publicly traded stocks using
Discounted Cash Flow (DCF) analysis. It fetches financial data from the
Morningstar API, runs a DCF model against that data, and produces an estimated
fair value per share — then exports a fully detailed, editable Excel workbook
for deeper analysis.

This was built as an early personal project to learn Python application
development and end-to-end: API integration, local data persistence, financial
modelling, GUI design, and file export.
This porject applis concepts I learned in collegiate finance classes

---

## How It Works

1. **Search** — Enter a company name or ticker. AutoValu queries the Morningstar
   API via RapidAPI and displays matching results in a table.

2. **Configure** — Select a company and set your DCF model parameters:
   - NWC calculation method (four options)
   - Projection period in years
   - Terminal growth rate
   - Risk-free rate of return (US Treasury yield — link provided in Help menu)
   - Expected market rate of return (Market Risk Premia — link provided in Help menu)

3. **Evaluate** — AutoValu runs three independent DCF evaluations:
   - **Historical** — margin assumptions derived from 5-year averages
   - **Recent** — margin assumptions derived from the most recent fiscal year
   - **Custom** — assumptions seeded from the average of Historical and Recent,
     intended to be edited in the exported Excel workbook

4. **Export** — Save the results to an Excel workbook containing:
   - A summary sheet with a valuation verdict across all three models
   - An editable model assumptions sheet linked to the DCF sheets
   - One detailed DCF sheet per evaluation type

---

## Running the Application

```bash
python controller.py
```

Requires Python 3.9+ and the dependencies listed in `requirements.txt`.

---

## Architecture

The project follows an MVC pattern:

| File | Role |
|------|------|
| `controller.py` | Entry point. Wires view and model together, handles navigation and caching logic. |
| `model.py` | Thin facade exposing all backend module classes as attributes. |
| `view.py` | All PyQt5 UI code — pages, widgets, and styles. |
| `modules/api.py` | Morningstar API calls and response parsing. |
| `modules/db.py` | SQLite caching of API responses and stored evaluations. |
| `modules/evaluation.py` | DCF engine — margins, cash flows, WACC, and fair value. |
| `modules/excel.py` | Formatted Excel workbook generation via openpyxl. |

Financial data is cached locally in `local_db/autovalu.db` so that repeated
lookups for the same company do not consume API quota.

---

## Strengths

- Automates the data-gathering and calculation steps of a DCF valuation,
  reducing a multi-hour manual process to a few minutes.
- Caches API responses across sessions to minimise redundant calls.
- Produces three evaluation types side-by-side for comparison, rather than
  committing to a single set of assumptions.
- Exports a fully editable Excel model so assumptions can be refined after
  the initial automated pass.

---

## Limitations

As an early project, AutoValu has several known shortcomings:

- **Hardcoded API key** — The RapidAPI key for Morningstar is embedded directly
  in `modules/api.py`. It should be moved to an environment variable or config
  file.
- **Fixed-resolution UI** — The window is locked to 1500×1200 pixels using
  absolute widget positions. It will not scale to different screen sizes or DPI
  settings.
- **No real authentication** — The login screen accepts any input and always
  proceeds. It is a placeholder with no actual access control.
- **Beta limited to NASDAQ** — Beta is always calculated relative to the NASDAQ
  index regardless of the company's exchange, which will produce inaccurate
  results for NYSE-listed companies.
- **No unit tests** — The calculation and data-parsing logic has no automated
  test coverage.
- **API dependency** — The application requires an active RapidAPI subscription
  to the Morningstar API. If the key expires or the endpoint changes, data
  fetching will fail.
