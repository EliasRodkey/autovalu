#! python3
"""
api.py - Morningstar API integration module for AutoValu.

Sends HTTP requests to the Morningstar API via RapidAPI and parses response
data into structured Python objects used by the evaluation engine.

Classes:
    APIData: Issues all Morningstar API calls and stores raw response data.
    DataValues: Parses a raw API data object into typed financial data attributes
                and computes derived values such as beta and effective tax rates.

Variables:
    headers (dict): RapidAPI authentication headers for all Morningstar requests.
    market_index (dict): Maps MIC exchange codes to Morningstar index tickers.
"""

import logging
import requests
import json
import webbrowser
import concurrent.futures as futures
from typing import Optional

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

headers = {
    "accept": "string",
    "x-rapidapi-key": "7133aa73afmsh9553e518d5fedaep18d31fjsna5dadc38dd6e",
    "x-rapidapi-host": "morningstar1.p.rapidapi.com",
}
market_index = {
    "XNAS": "126.1.NDAQ",
    "XNYS": "126.1.NYE",
}


class APIData:
    """Issues all Morningstar API calls and stores the raw response data.

    Attributes:
        search_results (list | None): Autocomplete results from the most recent search.
        company_profile (dict | None): Company profile from the most recent profile call.
        company_name (str): Name of the company queried via query_morningstar.
        mic (str): Market Identifier Code of the queried company.
        ticker (str): Exchange ticker symbol of the queried company.
        eod_ticker (str): End-of-day quote ticker of the queried company.
        fundamentals (list): 5 years of annual restated fundamental data.
        stock_data (list): Historical daily price data for the queried company.
        quarterly (list): 20 quarters of quarterly income statement data.
        NASDAQ_data (list): Historical daily price data for the NASDAQ index.
        stat_ratios (dict): Statistical key ratios for the queried company.
        fin_ratios (dict): Financial key ratios for the queried company.
        trailing_returns (dict): Trailing return data for the queried company.
        ms_valuations (dict): Morningstar valuation data for the queried company.

    Methods:
        __init__: Initialize empty result holders.
        query_morningstar: Fetch all financial data required for a DCF evaluation.
        auto_complete_call: Search for companies by name or ticker.
        company_profile_call: Fetch the company profile for a given ticker and MIC.
        fundamental_call: Fetch 5 years of annual restated fundamentals (static).
        quarterly_call: Fetch 20 quarters of quarterly income statement data (static).
        price_call: Fetch historical end-of-day price data (static).
        stat_ratio_call: Fetch statistical key ratios (static).
        fin_ratio_call: Fetch financial key ratios (static).
        trailing_returns_call: Fetch trailing return data (static).
        ms_valuations_call: Fetch Morningstar valuation data (static).
        companies_list_call: Fetch a list of all companies on an exchange (static).
        data_object: Package all fetched data into a single dictionary.
        find_risk_free: Open the US Treasury yield page in the default browser (static).
        find_expected_return: Open the Market Risk Premia page in the default browser (static).
    """

    def __init__(self) -> None:
        """Initialize empty holders for search results and company profile."""
        self.search_results: Optional[list] = None
        self.company_profile: Optional[dict] = None

    def query_morningstar(self, auto_complete_selection: dict) -> None:
        """Fetch all financial data required for a DCF evaluation.

        Calls each Morningstar endpoint sequentially and stores the results as
        instance attributes consumed by data_object().

        Args:
            auto_complete_selection (dict): A company entry from autocomplete results,
                containing 'companyName', 'mic', 'ticker', and 'endOfDayQuoteTicker'.
        """
        self.company_name = auto_complete_selection["companyName"]
        self.mic = auto_complete_selection["mic"]
        self.ticker = auto_complete_selection["ticker"]
        self.eod_ticker = auto_complete_selection["endOfDayQuoteTicker"]
        self.fundamentals = self.fundamental_call(self.mic, self.ticker)
        self.stock_data = self.price_call(self.mic, self.eod_ticker)
        self.quarterly = self.quarterly_call(self.mic, self.ticker)
        # self.NASDAQ_data = self.price_call(self.mic, market_index[self.mic])
        self.NASDAQ_data = self.price_call("XNAS", "126.1.NDAQ")
        self.stat_ratios = self.stat_ratio_call(self.mic, self.ticker)
        self.fin_ratios = self.fin_ratio_call(self.mic, self.ticker)
        self.trailing_returns = self.trailing_returns_call(self.mic, self.ticker)
        self.ms_valuations = self.ms_valuations_call(self.mic, self.ticker)

    def auto_complete_call(self, search: str) -> list:
        """Search for companies matching a name or ticker string.

        Args:
            search (str): The search text entered by the user.

        Returns:
            list: List of company result dicts, each containing 'companyName',
                  'ticker', 'mic', 'currency', 'securityId', and
                  'endOfDayQuoteTicker'.
        """
        logging.info("collecting search data from morningstar...")
        url = "https://rapidapi.p.rapidapi.com/companies/auto-complete-search"
        querystring = {"SearchText": str(search)}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        self.search_results = results
        return results

    def company_profile_call(self, mic: str, tkr: str) -> dict:
        """Fetch the company profile for a given ticker and MIC code.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            dict: Company profile containing 'sector', 'industry',
                  'businessDescription', 'contact', and related fields.
        """
        logging.info("collecting company profile from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/companies/get-company-profile"
        querystring = {"Ticker": str(tkr).upper(), "Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["result"]
        )
        self.company_profile = results
        return results

    @staticmethod
    def fundamental_call(mic: str, tkr: str) -> list:
        """Fetch 5 years of annual restated fundamental data from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            list: List of annual fundamental data dicts, one per fiscal year,
                  containing income statement, balance sheet, and cash flow data.
        """
        logging.info(
            "collecting 5 years of annual fundamentals restated from morningstar..."
        )
        url = "https://rapidapi.p.rapidapi.com/convenient/fundamentals/yearly/restated"
        querystring = {"Mic": str(mic).upper(), "Ticker": str(tkr).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    @staticmethod
    def quarterly_call(mic: str, tkr: str) -> list:
        """Fetch 20 quarters of quarterly income statement data from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            list: List of quarterly income statement dicts ordered oldest-first.
        """
        logging.info(
            "collecting 20 quarters of quarterly fundamentals restated from morningstar..."
        )
        url = "https://rapidapi.p.rapidapi.com/fundamentals/quarterly/income-statement/restated"
        querystring = {"Ticker": str(tkr).upper(), "Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    @staticmethod
    def price_call(mic: str, endOfDayQuoteTicker: str) -> list:
        """Fetch up to 10 years of historical end-of-day price data from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            endOfDayQuoteTicker (str): Morningstar end-of-day quote ticker.

        Returns:
            list: List of daily price dicts each containing 'date', 'open',
                  'high', 'low', 'last', and 'volume'.
        """
        logging.info("collecting 10 years of stock price data from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/endofdayquotes/history"
        querystring = {
            "Mic": str(mic).upper(),
            "EndOfDayQuoteTicker": str(endOfDayQuoteTicker),
        }
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    @staticmethod
    def stat_ratio_call(mic: str, tkr: str, trailing12: bool = False) -> list:
        """Fetch statistical key ratios from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').
            trailing12 (bool): If True, include trailing 12-month data. Defaults to False.

        Returns:
            list: List of statistical ratio data dicts.
        """
        logging.info("collecting statistical ratios from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/keyratios/statistics"
        querystring = {
            "Ticker": str(tkr).upper(),
            "Mic": str(mic).upper(),
            "IncludeTrailing12Months": str(trailing12).lower(),
        }
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    @staticmethod
    def fin_ratio_call(mic: str, tkr: str) -> list:
        """Fetch financial key ratios from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            list: List of financial ratio data dicts.
        """
        logging.info("collecting financial ratios from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/keyratios/financials"
        querystring = {"Ticker": str(tkr).upper(), "Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    @staticmethod
    def trailing_returns_call(mic: str, tkr: str) -> dict:
        """Fetch trailing return data from Morningstar.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            dict: Trailing return data keyed by time period.
        """
        logging.info("collecting trailing returns from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/live-stocks/GetRawTrailingReturns"
        querystring = {"Ticker": str(tkr).upper(), "Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        try:
            results = data["responseStatus"]
        except KeyError:
            results = data
        return results

    @staticmethod
    def ms_valuations_call(mic: str, tkr: str) -> dict:
        """Fetch Morningstar valuation data for a company.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').
            tkr (str): Exchange ticker symbol (e.g. 'AAPL').

        Returns:
            dict: Morningstar valuation metrics keyed by metric name.
        """
        logging.info("collecting valuations from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/live-stocks/GetValuation"
        querystring = {"Ticker": str(tkr).upper(), "Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        try:
            results = data["responseStatus"]
        except KeyError:
            results = data
        return results

    @staticmethod
    def companies_list_call(mic: str) -> list:
        """Fetch a list of all companies listed on a given exchange.

        Args:
            mic (str): Market Identifier Code (e.g. 'XNAS').

        Returns:
            list: List of company summary dicts for every security on the exchange.
        """
        logging.info("collecting list of companies from morningstar...")
        url = "https://morningstar1.p.rapidapi.com/companies/list-by-exchange"
        querystring = {"Mic": str(mic).upper()}
        response = requests.request(
            "GET", url, headers=headers, params=querystring
        ).content
        data = json.loads(response)
        results = (
            data["responseStatus"]
            if (data["responseStatus"] != None)
            else data["results"]
        )
        return results

    def data_object(self) -> dict:
        """Package all fetched API data into a single dictionary for storage or parsing.

        Returns:
            dict: Dictionary with keys 'fundamentals', 'quarterly', 'stock_data',
                  'NASDAQ_data', 'stat_ratios', 'fin_ratios', 'trailing_returns',
                  'ms_valuations', and 'profile'.
        """
        to_db = {
            "fundamentals": self.fundamentals,
            "quarterly": self.quarterly,
            "stock_data": self.stock_data,
            "NASDAQ_data": self.NASDAQ_data,
            "stat_ratios": self.stat_ratios,
            "fin_ratios": self.fin_ratios,
            "trailing_returns": self.trailing_returns,
            "ms_valuations": self.ms_valuations,
            "profile": self.company_profile,
        }
        return to_db

    @staticmethod
    def find_risk_free() -> None:
        """Open the US Treasury yield page in the default browser."""
        logging.info(
            "helping you find the risk free rate of return, check your browser..."
        )
        url = "https://www.treasury.gov/resource-center/data-chart-center/interest-rates/pages/TextView.aspx?data=yield"
        webbrowser.open(url)

    @staticmethod
    def find_expected_return() -> None:
        """Open the Market Risk Premia page in the default browser."""
        logging.info(
            "helping you find the expected market rate of return, check your browser..."
        )
        url = "http://www.market-risk-premia.com/us.html"
        webbrowser.open(url)


if __name__ == "__main__":
    pass


class DataValues:
    """Parses a raw API data object into typed financial attributes and computes derived values.

    Attributes:
        company_name (str): Name of the company.
        ticker (str): Exchange ticker symbol.
        mic (str): Market Identifier Code.
        fundamentals (list): Raw annual fundamental data from the API.
        stock_data (list): Raw historical daily price data for the company.
        profile (dict): Raw company profile data from the API.
        NASDAQ_data (list): Raw historical daily price data for the NASDAQ index.
        start_date (tuple): Fiscal year start dates across the 5-year period.
        revenue (tuple[float, ...]): Annual revenue figures.
        cost_of_revenue (tuple[float, ...]): Annual cost of revenue figures.
        ebitda (tuple[float, ...]): Annual EBITDA figures.
        interest_expense (tuple[float, ...]): Annual interest expense figures.
        ebit (tuple[float, ...]): Annual income before taxes figures.
        taxes (tuple[float, ...]): Annual income tax provision figures.
        net_income (tuple[float, ...]): Annual net income figures.
        dpn_and_am (tuple[float, ...]): Annual depreciation and amortization figures.
        dnwc (tuple[float, ...]): Annual change in working capital figures.
        capex (tuple[float, ...]): Annual capital expenditure figures.
        cash_and_equiv (tuple[float, ...]): Annual cash and cash equivalents.
        total_cash (tuple[float, ...]): Annual total cash figures.
        receivables (tuple[float, ...]): Annual accounts receivable figures.
        inventories (tuple[float, ...]): Annual inventory figures.
        tca (tuple[float, ...]): Annual total current assets.
        ta (tuple[float, ...]): Annual total assets.
        short_term_debt (tuple[float, ...]): Annual short-term debt figures.
        payables (tuple[float, ...]): Annual accounts payable figures.
        tcl (tuple[float, ...]): Annual total current liabilities.
        long_term_debt (tuple[float, ...]): Annual long-term debt figures.
        tl (tuple[float, ...]): Annual total liabilities.
        shareholder_eq (tuple[float, ...]): Annual total stockholders' equity.
        tl_and_eq (tuple[float, ...]): Annual total liabilities and equity.
        wavgshares (tuple[float, ...]): Annual diluted weighted average shares outstanding.
        excess_cash (list[float]): Annual excess cash (cash minus current liabilities, floored at 0).
        tax_rates (list[float]): Annual effective tax rates.
        beta (float): Calculated beta relative to the NASDAQ index.
        stock_table (tuple): Historical price data as a tuple of (date, open, high, low, last, volume).
        current_price (dict): Most recent daily price entry.
        description (str): Company business description.
        industry (str): Company industry classification.
        sector (str): Company sector classification.
        website (str): Company website URL.

    Methods:
        __init__: Parse the API data object and compute all derived attributes.
        list_value_finder: Extract a time-series of a nested value from annual fundamentals.
        calculate_beta: Compute beta relative to the NASDAQ index.
        eff_tax_rates: Compute the effective tax rate for each of the 5 fiscal years.
        calc_covariance: Compute the covariance of daily returns between two price series.
        make_equal_length: Align two price series to a common set of trading dates.
        make_dictionary: Build a date-indexed dictionary from a price series (static).
        update_dictionary: Add a second price series into an existing date dictionary (static).
        remove_unique_dates: Remove entries that appear in only one of the two series (static).
        calc_variance: Compute the variance of daily returns for a price series (static).
        percent_change: Compute the daily percent change series for a price array (static).
        list_average: Compute the average of a specific key across a list of dicts (static).
    """

    def __init__(self, chosen_company: dict, data_object: dict) -> None:
        """Parse the API data object and compute all derived financial attributes.

        Args:
            chosen_company (dict): Company identifier fields selected by the user,
                containing 'companyName', 'ticker', and 'mic'.
            data_object (dict): Raw API data as returned by APIData.data_object().
        """
        self.company_name = chosen_company["companyName"]
        self.ticker = chosen_company["ticker"]
        self.mic = chosen_company["mic"]
        self.fundamentals = data_object["fundamentals"]
        self.stock_data = data_object["stock_data"]
        self.profile = data_object["profile"]
        self.NASDAQ_data = data_object["NASDAQ_data"]

        ###   Fundamentals Data   ###
        self.start_date = self.list_value_finder("startDate")
        # Income statement data attributes
        self.revenue = self.list_value_finder("incomeStatement", "revenue")
        self.cost_of_revenue = self.list_value_finder(
            "incomeStatement", "costOfRevenue"
        )
        self.ebitda = self.list_value_finder("incomeStatement", "ebitda")
        self.interest_expense = self.list_value_finder(
            "incomeStatement", "interestExpense"
        )
        self.ebit = self.list_value_finder("incomeStatement", "incomeBeforeTaxes")
        self.taxes = self.list_value_finder(
            "incomeStatement", "provisionOrBenefitForIncomeTaxes"
        )
        self.net_income = self.list_value_finder("incomeStatement", "netIncome")

        # Statement of cash flows data attributes
        self.dpn_and_am = self.list_value_finder(
            "cashflowStatement", "operatingActivity", "depreciationAndAmortization"
        )
        self.dnwc = self.list_value_finder(
            "cashflowStatement", "operatingActivity", "changeInWorkingCapital"
        )
        self.capex = self.list_value_finder(
            "cashflowStatement", "freeCashFlow", "capitalExpenditure"
        )

        # Balance sheet data attributes
        # Assets
        self.cash_and_equiv = self.list_value_finder(
            "balanceSheet",
            "assets",
            "commercialsCurrentAssets",
            "cash",
            "cashAndCashEquivalents",
        )
        self.total_cash = self.list_value_finder(
            "balanceSheet", "assets", "commercialsCurrentAssets", "cash", "totalCash"
        )
        self.receivables = self.list_value_finder(
            "balanceSheet", "assets", "commercialsCurrentAssets", "receivables"
        )
        self.inventories = self.list_value_finder(
            "balanceSheet", "assets", "commercialsCurrentAssets", "inventories"
        )
        self.tca = self.list_value_finder(
            "balanceSheet", "assets", "commercialsCurrentAssets", "totalCurrentAssets"
        )
        self.ta = self.list_value_finder("balanceSheet", "assets", "totalAssets")
        # Liabilities
        self.short_term_debt = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "liabilities",
            "currentLiabilities",
            "shortTermDebt",
        )
        self.payables = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "liabilities",
            "currentLiabilities",
            "accountsPayable",
        )
        self.tcl = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "liabilities",
            "currentLiabilities",
            "totalCurrentLiabilities",
        )
        self.long_term_debt = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "liabilities",
            "noncurrentLiabilities",
            "longTermDebt",
        )
        self.tl = self.list_value_finder(
            "balanceSheet", "liabAndStockEquity", "liabilities", "totalLiabilities"
        )
        # Equity
        self.shareholder_eq = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "stockholdersEquity",
            "totalStockholdersEquity",
        )
        self.tl_and_eq = self.list_value_finder(
            "balanceSheet",
            "liabAndStockEquity",
            "totalLiabilitiesAndStockholdersEquity",
        )
        self.wavgshares = self.list_value_finder(
            "incomeStatement", "weightedAvgShares", "diluted"
        )
        self.excess_cash = []
        for i in range(len(self.fundamentals)):
            self.excess_cash.append(max(0, (self.cash_and_equiv[i] - self.tcl[i])))

        # Effective tax rate
        self.tax_rates = self.eff_tax_rates()

        # Beta
        self.beta = self.calculate_beta()

        ###   Stock Price Data   ###
        stock_li = []
        for day in self.stock_data:
            tup = (
                day["date"],
                day["open"],
                day["high"],
                day["low"],
                day["last"],
                day["volume"],
            )
            stock_li.append(tup)
        self.stock_table = tuple(stock_li)
        self.current_price = self.stock_data[-1]

        ###   Company profile data   ###
        self.description = self.profile["businessDescription"]["value"]
        self.industry = self.profile["industry"]["value"]
        self.sector = self.profile["sector"]["value"]
        self.website = self.profile["contact"]["url"]

    def list_value_finder(self, *args: str) -> tuple:
        """Extract a time-series of a nested value from the annual fundamentals list.

        Traverses each year's fundamental dict using the provided key sequence and
        collects the terminal value into a tuple ordered oldest-to-most-recent.

        Args:
            *args (str): Sequence of dict keys describing the path to the target value.

        Returns:
            tuple: One value per fiscal year, ordered oldest to most recent.
        """
        # TODO: add ticker to debug string
        logging.debug("finding {}...".format(args[-1]))
        li = []
        for year in self.fundamentals:
            for arg in args:
                year = year[arg]
            li.append(year)
        return tuple(li)

    def calculate_beta(self) -> float:
        """Compute the company's beta relative to the NASDAQ index.

        Returns:
            float: Beta coefficient rounded to two decimal places.
        """
        logging.info("calculating beta...")
        covariance = self.calc_covariance(self.stock_data, self.NASDAQ_data)
        variance = DataValues.calc_variance(self.NASDAQ_data)
        beta = covariance / variance
        return round(beta, 2)

    def eff_tax_rates(self) -> list[float]:
        """Compute the effective tax rate for each of the 5 fiscal years.

        Returns:
            list[float]: Effective tax rates (taxes / EBIT) for each of the 5 years.
        """
        tax_rate = []
        for i in range(5):
            tax_rate.append(self.taxes[i] / self.ebit[i])
        return tax_rate

    def calc_covariance(self, array1: list, array2: list) -> float:
        """Compute the covariance of daily returns between two price series.

        Aligns the two arrays to a common set of trading dates before computing.

        Args:
            array1 (list): Daily price dicts for the first security.
            array2 (list): Daily price dicts for the second security (e.g. index).

        Returns:
            float: Sample covariance of the two daily return series.
        """
        combined = (array1, array2)
        if len(array1) != len(array2):
            array1, array2 = self.make_equal_length(array1, array2)

        len_array = len(array1) if len(array1) == len(array2) else None
        if len_array == None:
            logging.critical("arrays of unequal length, cannot calculate beta")
        array1_avg = DataValues.list_average(combined[0], "last")
        array2_avg = DataValues.list_average(combined[1], "last")

        array1_pct_chg = DataValues.percent_change(combined[0], "last")
        array2_pct_chg = DataValues.percent_change(combined[1], "last")

        total = 0
        for day in zip(array1_pct_chg, array2_pct_chg):
            num = (day[0] - array1_avg) * (day[1] - array2_avg)
            total += num
        covariance = total / (len_array - 1)
        return covariance

    def make_equal_length(self, security_array: list, index_array: list) -> tuple[list, list]:
        """Align two price series to a common set of trading dates.

        Removes dates that appear in only one of the two series so that both
        arrays share identical date coverage before covariance is computed.

        Args:
            security_array (list): Daily price dicts for the company.
            index_array (list): Daily price dicts for the market index.

        Returns:
            tuple[list, list]: The two aligned price arrays with mismatched dates removed.
        """
        dictionary = self.make_dictionary(security_array)
        new_dictionary = self.update_dictionary(dictionary, index_array)
        security_array, index_array = self.remove_unique_dates(
            new_dictionary, security_array, index_array
        )
        import pprint
        pprint.pprint(zip(security_array, index_array))
        return security_array, index_array

    @staticmethod
    def make_dictionary(array_of_json_1: list) -> dict:
        """Build a date-indexed dictionary from a price series.

        Args:
            array_of_json_1 (list): Daily price dicts, each containing a 'date' key.

        Returns:
            dict: Mapping of date string to {'inst': 1, 'index_1': i}.
        """
        dictionary = {}
        for i, obj in enumerate(array_of_json_1):
            dictionary[obj["date"]] = {"inst": 1, "index_1": i}
        return dictionary

    @staticmethod
    def update_dictionary(dictionary: dict, array_of_json_2: list) -> dict:
        """Add a second price series into an existing date dictionary.

        For each date in array_of_json_2, increments 'inst' if the date already
        exists or creates a new entry otherwise.

        Args:
            dictionary (dict): Existing date dictionary from make_dictionary.
            array_of_json_2 (list): Daily price dicts for the second series.

        Returns:
            dict: Updated dictionary with entries from both price series.
        """
        for i, obj in enumerate(array_of_json_2):
            date = obj["date"]
            if date in dictionary.keys():
                dictionary[date]["inst"] += 1
                dictionary[date]["index_2"] = i
            else:
                dictionary[date] = {"inst": 1, "index_2": i}
        return dictionary

    @staticmethod
    def remove_unique_dates(dictionary: dict, array_1: list, array_2: list) -> tuple[list, list]:
        """Remove entries that appear in only one of the two price series.

        Args:
            dictionary (dict): Date dictionary produced by update_dictionary.
            array_1 (list): Daily price dicts for the first series.
            array_2 (list): Daily price dicts for the second series.

        Returns:
            tuple[list, list]: Both arrays with unique-date entries removed.
        """
        for date in dictionary:
            date = dictionary[date]
            if date["inst"] == 1:
                try:
                    i = date["index_1"]
                    del array_1[i]
                except KeyError:
                    i = date["index_2"]
                    del array_2[i]
            else:
                pass
        return array_1, array_2

    @staticmethod
    def calc_variance(data_array: list) -> float:
        """Compute the sample variance of daily returns for a price series.

        Args:
            data_array (list): Daily price dicts each containing a 'last' key.

        Returns:
            float: Sample variance of the daily return series.
        """
        data_avg = DataValues.list_average(data_array, "last")
        data_percent = DataValues.percent_change(data_array, "last")

        total = 0.0
        for day in data_percent:
            num = (day - data_avg) ** 2
            total += num

        return total / (len(data_array) - 1)

    @staticmethod
    def percent_change(data_array: list, dict_value: str) -> tuple[float, ...]:
        """Compute the daily percent change series for a price array.

        Args:
            data_array (list): List of daily price dicts.
            dict_value (str): Key to extract the price value from each dict (e.g. 'last').

        Returns:
            tuple[float, ...]: Daily percent change values, length is len(data_array) - 1.
        """
        percent_change = []
        for index, day in enumerate(data_array):
            if index == 0:
                pass
            else:
                percent_change.append(
                    (day[dict_value] - data_array[index - 1][dict_value])
                    / data_array[index - 1][dict_value]
                )
        return tuple(percent_change)

    @staticmethod
    def list_average(li: list, dict_value: str) -> float:
        """Compute the average of a specific key across a list of dicts.

        Args:
            li (list): List of dicts each containing dict_value.
            dict_value (str): Key whose values are averaged.

        Returns:
            float: Arithmetic mean of the extracted values.
        """
        total = 0
        for item in li:
            num = item[dict_value]
            total += num
        return total / len(li)
