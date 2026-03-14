#! python3
"""
seed_db.py - One-time script to populate AutoValu's SQLite database with real
Apple (AAPL) financial data fetched from Yahoo Finance.

Run once before launching the app:
    pip install yfinance
    python seed_db.py

After running, launch the app normally:
    python controller.py

Then search "apple" on the search page, or click History to load the
saved evaluation directly.
"""

import copy
import os
import sys

# Ensure the working directory is the repo root so DBHandler finds local_db/
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
    import yfinance as yf
except ImportError:
    print("Please install yfinance first:  pip install yfinance")
    sys.exit(1)

from modules.db import DBHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_int(val, default=0):
    """Return int(val) or default when val is NaN / None / unconvertible."""
    try:
        if pd.isna(val):
            return default
        return int(val)
    except (TypeError, ValueError):
        return default


def _get(series, field, default=0):
    """Get a field from a pandas Series by label, returning default if absent."""
    val = series.get(field, None)
    if val is None:
        return default
    return _safe_int(val, default)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_fundamentals(income, balance, cashflow):
    """
    Build a 5-element list of annual fundamental dicts in Morningstar format.

    yfinance DataFrames have columns ordered most-recent first.  We reverse
    so the list is oldest-first (matching the Morningstar API convention).
    If fewer than 5 years are available the oldest year is duplicated to pad.
    """
    n = min(len(income.columns), len(balance.columns), len(cashflow.columns))

    fundamentals = []
    # i = 0 is the most recent year; iterate n-1 → 0 to build oldest-first
    for i in range(n - 1, -1, -1):
        col_date = income.columns[i]
        inc = income.iloc[:, i]
        bal = balance.iloc[:, i] if i < len(balance.columns) else pd.Series(dtype=float)
        cf  = cashflow.iloc[:, i] if i < len(cashflow.columns) else pd.Series(dtype=float)

        end_date   = col_date.strftime("%Y-%m-%d")
        start_date = col_date.replace(year=col_date.year - 1).strftime("%Y-%m-%d")

        year_dict = {
            "startDate": start_date,
            "endDate":   end_date,
            "includesTrailing12Months": False,
            "incomeStatement": {
                "revenue":                                 _get(inc, "Total Revenue"),
                "costOfRevenue":                           _get(inc, "Cost Of Revenue"),
                "ebitda":                                  _get(inc, "EBITDA"),
                "interestExpense":                         abs(_get(inc, "Interest Expense")),
                "incomeBeforeTaxes":                       _get(inc, "Pretax Income"),
                "provisionOrBenefitForIncomeTaxes":        _get(inc, "Tax Provision"),
                "netIncome":                               _get(inc, "Net Income"),
                "weightedAvgShares": {
                    "diluted": _get(inc, "Diluted Average Shares"),
                },
            },
            "cashflowStatement": {
                "operatingActivity": {
                    "depreciationAndAmortization": _get(cf, "Depreciation And Amortization"),
                    "changeInWorkingCapital":      _get(cf, "Change In Working Capital"),
                },
                "freeCashFlow": {
                    "capitalExpenditure": _get(cf, "Capital Expenditure"),
                },
            },
            "balanceSheet": {
                "assets": {
                    "commercialsCurrentAssets": {
                        "cash": {
                            "cashAndCashEquivalents": _get(bal, "Cash And Cash Equivalents"),
                            "totalCash": _get(
                                bal,
                                "Cash Cash Equivalents And Short Term Investments",
                                _get(bal, "Cash And Cash Equivalents"),
                            ),
                        },
                        "receivables":       _get(bal, "Receivables"),
                        "inventories":       _get(bal, "Inventory"),
                        "totalCurrentAssets": _get(bal, "Current Assets"),
                    },
                    "totalAssets": _get(bal, "Total Assets"),
                },
                "liabAndStockEquity": {
                    "liabilities": {
                        "currentLiabilities": {
                            "shortTermDebt":          _get(bal, "Current Debt"),
                            "accountsPayable":        _get(bal, "Accounts Payable"),
                            "totalCurrentLiabilities": _get(bal, "Current Liabilities"),
                        },
                        "noncurrentLiabilities": {
                            "longTermDebt": _get(bal, "Long Term Debt"),
                        },
                        "totalLiabilities": _get(bal, "Total Liabilities Net Minority Interest"),
                    },
                    "stockholdersEquity": {
                        "totalStockholdersEquity": _get(bal, "Stockholders Equity"),
                    },
                    "totalLiabilitiesAndStockholdersEquity": _get(bal, "Total Assets"),
                },
            },
        }
        fundamentals.append(year_dict)

    # Drop years where revenue is 0 — yfinance sometimes returns an incomplete oldest year
    fundamentals = [yr for yr in fundamentals if yr["incomeStatement"]["revenue"] != 0]

    # Pad to exactly 5 years — eff_tax_rates() always iterates range(5)
    while len(fundamentals) < 5:
        fundamentals.insert(0, copy.deepcopy(fundamentals[0]))

    return fundamentals[:5]


def build_price_series(history_df):
    """Convert a yfinance history DataFrame to the Morningstar price-list format."""
    records = []
    for date, row in history_df.iterrows():
        records.append({
            "date":   date.strftime("%Y-%m-%d"),
            "open":   round(float(row["Open"]),  4),
            "high":   round(float(row["High"]),  4),
            "low":    round(float(row["Low"]),   4),
            "last":   round(float(row["Close"]), 4),
            "volume": int(row["Volume"]),
        })
    return records


def build_profile(info):
    """Build a Morningstar-shaped company profile dict from yfinance info."""
    address = ", ".join(filter(None, [
        info.get("address1", ""),
        info.get("city", ""),
        info.get("state", ""),
        info.get("zip", ""),
    ]))
    return {
        "performanceId": info.get("uuid", ""),
        "title": "Company Profile",
        "businessDescription": {
            "label": "Business Description",
            "value": info.get("longBusinessSummary", ""),
        },
        "contact": {
            "label":    "Contact",
            "address1": address,
            "address2": "",
            "country":  info.get("country", ""),
            "phone":    info.get("phone", ""),
            "fax":      "",
            "email":    "",
            "url":      info.get("website", ""),
        },
        "fiscalYearEnds":       {"label": "Fiscal Year End",            "value": ""},
        "industry":             {"label": "Industry",                   "value": info.get("industry", "")},
        "sector":               {"label": "Sector",                     "value": info.get("sector", "")},
        "mostRecentEarnings":   {"label": "Most Recent Earnings",       "value": ""},
        "totalEmployees":       {"label": "Total Number of Employees",  "value": str(info.get("fullTimeEmployees", ""))},
        "endOfDayQuoteTickerId": "126.1.AAPL",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    stock_id = {
        "companyName":        "Apple Inc",
        "ticker":             "AAPL",
        "mic":                "XNAS",
        "currency":           "USD",
        "securityId":         "0P000000GY",
        "endOfDayQuoteTicker": "126.1.AAPL",
    }

    default_inputs = {
        "nwc_method":       "As Reported",
        "proj_years":       5,
        "terminal_growth":  2.5,
        "risk_free_rate":   4.5,
        "market_return":    10.0,
    }

    # --- Check for existing record -------------------------------------------
    db = DBHandler()
    existing = db.load_searches("apple")
    if existing is not None:
        print("Seed data already present (search 'apple' found in DB).")
        print("Delete local_db/autovalu.db and re-run to reset.")
        return

    # --- Fetch ---------------------------------------------------------------
    print("Fetching Apple (AAPL) data from Yahoo Finance...")
    aapl = yf.Ticker("AAPL")
    ixic = yf.Ticker("^IXIC")

    print("  Annual financials...")
    income   = aapl.income_stmt
    balance  = aapl.balance_sheet
    cashflow = aapl.cashflow

    print("  Company info...")
    info = aapl.info

    print("  Price history (10 years)...")
    aapl_hist = aapl.history(period="10y")
    ixic_hist = ixic.history(period="10y")

    if income.empty or balance.empty or cashflow.empty:
        print("ERROR: Could not fetch financial data from Yahoo Finance.")
        print("Check your internet connection and try again.")
        sys.exit(1)

    # --- Transform -----------------------------------------------------------
    print("Transforming to app format...")
    fundamentals = build_fundamentals(income, balance, cashflow)

    # Sanity check — non-zero values here confirm yfinance field names matched correctly.
    # If you see all zeros, the field names in build_fundamentals() need updating.
    print("  Fundamentals sanity check (should be non-zero for Apple):")
    for i, yr in enumerate(fundamentals):
        ebit = yr["incomeStatement"]["incomeBeforeTaxes"]
        tax  = yr["incomeStatement"]["provisionOrBenefitForIncomeTaxes"]
        rev  = yr["incomeStatement"]["revenue"]
        print(f"    Year {i} ({yr['endDate']}): revenue={rev:,}  pretaxIncome={ebit:,}  taxes={tax:,}")

    stock_data   = build_price_series(aapl_hist)
    nasdaq_data  = build_price_series(ixic_hist)
    profile      = build_profile(info)

    company_data = {
        "fundamentals":    fundamentals,
        "quarterly":       [],
        "stock_data":      stock_data,
        "NASDAQ_data":     nasdaq_data,
        "stat_ratios":     [],
        "fin_ratios":      [],
        "trailing_returns": {},
        "ms_valuations":   {},
        "profile":         profile,
    }

    # --- Insert --------------------------------------------------------------
    print("Writing to database...")
    os.makedirs("local_db", exist_ok=True)
    db.make_search_inst("apple", [stock_id])
    db.make_profile_inst(stock_id["securityId"], profile)
    db.make_data_inst(stock_id, company_data, default_inputs)

    print("\nDone!  Run `python controller.py` to launch the app.")
    print("  Search 'apple' on the search page, or click History to")
    print("  load the pre-saved Apple evaluation directly.")


if __name__ == "__main__":
    main()
