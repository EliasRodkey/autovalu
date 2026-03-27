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
  fetching will fail. The API used is also no longer available on RapidAPI.

## Future Changes

### Overview
This project is old, and upon revisiting there are several places where it could be improved in the future.

### API Abstraction Layer
The api.py module relies solely on the "morningstar1" RapidAPI.com api subscription.
This particular API has been decomissioned and no longer works. The different API methods
used in this project should be associated with an abstract class that different APIs can
interface with to allow switching in case one goes offline or a better one becomes available.

### view.py Refactoring Ideas
`view.py` is the largest file in the project (~868 lines) and was originally
auto-generated from a Qt Designer `.ui` file. It works but has several structural
and maintainability issues worth addressing in a future pass.

#### File Structure
All five page classes (`LoginPage`, `SearchPage`, `InputPage`, `SummaryPage`,
`AboutPage`), the main window class (`Ui_View`), the error dialog (`ErrorPopup`),
and the style helper (`QtStyle`) live in a single file. Splitting each page into
its own module under a `views/` package would make individual pages easier to
find, read, and test in isolation.

#### Qt Model-View Separation
The search results table uses `QStandardItemModel` with manually populated rows.
Subclassing `QAbstractTableModel` with the search results list as its data source
would be a cleaner separation of data and presentation, and would make the table
easier to sort, filter, and test.

#### Docstrings and Type Hints
Once the layout and structure issues above are addressed, add module, class, and
method docstrings with type hints following the same format used in the rest of
the codebase.

### Working Sign In
The skeleton sign in page is a clear missing feature. Implementing real user sign in, or removing it entirely should be considered in the future.
