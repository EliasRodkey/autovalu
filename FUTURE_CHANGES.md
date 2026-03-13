# Future Changes

## Overview
This project is old, and upon revisiting there are several places where it could be improved in the future.

## API Abstraction Layer
The api.py module relies solely on the "morningstar1" RapidAPI.com api subscription.
This particular API has been decomissioned and no longer works. The different API methods
used in this project should be associated with an abstract class that different APIs can
interface with to allow switching in case one goes offline or a better one becomes available.

## view.py Refactoring Ideas
`view.py` is the largest file in the project (~868 lines) and was originally
auto-generated from a Qt Designer `.ui` file. It works but has several structural
and maintainability issues worth addressing in a future pass.

### File Structure
All five page classes (`LoginPage`, `SearchPage`, `InputPage`, `SummaryPage`,
`AboutPage`), the main window class (`Ui_View`), the error dialog (`ErrorPopup`),
and the style helper (`QtStyle`) live in a single file. Splitting each page into
its own module under a `views/` package would make individual pages easier to
find, read, and test in isolation.

### Qt Model-View Separation
The search results table uses `QStandardItemModel` with manually populated rows.
Subclassing `QAbstractTableModel` with the search results list as its data source
would be a cleaner separation of data and presentation, and would make the table
easier to sort, filter, and test.

### Docstrings and Type Hints
Once the layout and structure issues above are addressed, add module, class, and
method docstrings with type hints following the same format used in the rest of
the codebase.
