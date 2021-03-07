#! python3
# api_module.py - module that defines api call elements of application
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

import requests, json, webbrowser
import concurrent.futures as futures

headers = {
    "accept": "string",
    "x-rapidapi-key": "7133aa73afmsh9553e518d5fedaep18d31fjsna5dadc38dd6e",
    "x-rapidapi-host": "morningstar1.p.rapidapi.com",
}
market_index = {
    "XNAS" : "126.1.NDAQ",
    "XNYS" : "126.1.NYE"
}


class APIData:
    def __init__(self):
        self.search_results = None
        self.company_profile = None

    def query_morningstar(self, auto_complete_selection):
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

    def auto_complete_call(self, search):
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

    def company_profile_call(self, mic, tkr):
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
    def fundamental_call(mic, tkr):
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
    def quarterly_call(mic, tkr):
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
    def price_call(mic, endOfDayQuoteTicker):
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
    def stat_ratio_call(mic, tkr, trailing12=False):
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
    def fin_ratio_call(mic, tkr):
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
    def trailing_returns_call(mic, tkr):
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
    def ms_valuations_call(mic, tkr):
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
    def companies_list_call(mic):
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

    def data_object(self):
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
    def find_risk_free():
        logging.info(
            "helping you find the risk free rate of return, check your browser..."
        )
        url = "https://www.treasury.gov/resource-center/data-chart-center/interest-rates/pages/TextView.aspx?data=yield"
        webbrowser.open(url)

    @staticmethod
    def find_expected_return():
        logging.info(
            "helping you find the expected market rate of return, check your browser..."
        )
        url = "http://www.market-risk-premia.com/us.html"
        webbrowser.open(url)


if __name__ == "__main__":
    # with open("C:\\Users\\eliro\\OneDrive\\Documents\\Programming\\Applications\\AutoValu\\modules\\nasdaq_data.py", "w") as f:
    #     f.write(json.dumps(data.stock_data, indent=4))
    # with open("C:\\Users\\eliro\\OneDrive\\Documents\\Programming\\Applications\\AutoValu\\modules\\price_data.py", "w") as f:
    #     f.write(json.dumps(data.NASDAQ_data, indent=4))
    pass


class DataValues:
    def __init__(self, chosen_company, data_object):
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

    def list_value_finder(self, *args):
        # TODO: add ticker to debug string
        logging.debug("finding {}...".format(args[-1]))
        li = []
        for year in self.fundamentals:
            for arg in args:
                year = year[arg]
            li.append(year)
        return tuple(li)

    def calculate_beta(self):
        logging.info("calculating beta...")
        covariance = self.calc_covariance(self.stock_data, self.NASDAQ_data)
        variance = DataValues.calc_variance(self.NASDAQ_data)
        beta = covariance / variance
        return round(beta, 2)

    def eff_tax_rates(self):
        tax_rate = []
        for i in range(5):
            tax_rate.append(self.taxes[i] / self.ebit[i])
        return tax_rate

    def calc_covariance(self, array1, array2):
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
            # print(num)
            total += num
        covariance = total / (len_array - 1)
        return covariance

    def make_equal_length(self, security_array, index_array):
        dictionary = self.make_dictionary(security_array)
        new_dictionary = self.update_dictionary(dictionary, index_array)
        security_array, index_array = self.remove_unique_dates(
            new_dictionary, security_array, index_array
        )
        import pprint
        pprint.pprint(zip(security_array, index_array))
        return security_array, index_array

    @staticmethod
    def make_dictionary(array_of_json_1):
        dictionary = {}
        for i, obj in enumerate(array_of_json_1):
            dictionary[obj["date"]] = {"inst" : 1, "index_1" : i}
        return dictionary

    @staticmethod
    def update_dictionary(dictionary, array_of_json_2):
        for i, obj in enumerate(array_of_json_2):
            date = obj["date"]
            if date in dictionary.keys():
                dictionary[date]["inst"] += 1
                dictionary[date]["index_2"] = i
            else:
                dictionary[date] = {"inst" : 1, "index_2" : i}
        return dictionary
    
    @staticmethod
    def remove_unique_dates(dictionary, array_1, array_2):
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
    def calc_variance(data_array):
        data_avg = DataValues.list_average(data_array, "last")
        data_percent = DataValues.percent_change(data_array, "last")

        total = 0.0
        for day in data_percent:
            num = (day - data_avg) ** 2
            total += num

        return total / (len(data_array) - 1)

    @staticmethod
    def percent_change(data_array, dict_value):
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
    def list_average(li, dict_value):
        total = 0
        for item in li:
            num = item[dict_value]
            total += num
        return total / len(li)
