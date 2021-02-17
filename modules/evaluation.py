#! python3
# evl_module.py - module that defines evaluation attributes and methods
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

eval_types = ("Historical", "Recent", "Custom")
nwc_methods = (
    "As Reported",
    "(TCA-Cash)-(TCL-Debt)",
    "(A/R+Inventories-A/P)",
    "(TCA-TCL)",
)


class Functions:
    def __init__(self, eval_type, data_class, custom=False, values=None):
        if custom:
            self.tax_rate = self.as_percent(values["tax rate"])
        else:
            self.tax_rate = self.find_tax_rate(eval_type, data_class)

    def find_tax_rate(self, eval_type, data_class):
        logging.debug("calculating {} effective tax rate".format(eval_type))
        if eval_type == eval_types[0]:
            return self.list_avg(data_class.tax_rates)
        else:
            return data_class.tax_rates[-1]

    @staticmethod
    def as_percent(number):
        percent = number / 100
        return percent

    @staticmethod
    def list_avg(li):
        total = 0
        for i in li:
            total += i
        return total / len(li)

    @staticmethod
    def display_percent(decimal):
        return "{}%".format(round(decimal * 100, 2))

    @staticmethod
    def display_dollars(amount):
        return "${}".format(round(amount, 2))

    @staticmethod
    def display_million(amount):
        return "${}M".format(round(amount / 10 ** 6, 2))


class Margins(Functions):
    def __init__(self, eval_type, data_class, nwc_method, custom=False, values=None):
        Functions.__init__(self, eval_type, data_class, custom=custom, values=values)
        self.eval_type = eval_type
        self.data = data_class
        self.nwc_method = nwc_method
        self.sales_growth = self.find_sales_growth()
        self.ebitda_pct_rev = self.find_ebitda_as_percent()
        self.dpn_pct_rev = self.find_dpn_as_percent()
        self.past_nwc = self.get_nwc()
        self.nwc_pct_rev = self.find_nwc_as_percent()
        self.capex_pct_rev = self.find_capex_as_percent()
        if custom:
            self.sales_growth = self.as_percent(values["sales growth"])
            self.ebitda_pct_rev = self.as_percent(values["ebitda"])
            self.dpn_pct_rev = self.as_percent(values["dpn"])
            self.nwc_pct_rev = self.as_percent(values["nwc"])
            self.capex_pct_rev = self.as_percent(values["capex"])

    def find_sales_growth(self):
        logging.debug("calculating {} sales growth...".format(self.eval_type))
        if self.eval_type == eval_types[0]:
            hist_sales_growth = []
            for i in range(len(self.data.revenue) - 1):
                hist_sales_growth.append(
                    (self.data.revenue[i + 1] / self.data.revenue[i]) - 1
                )
            return self.list_avg(hist_sales_growth)
        elif self.eval_type == eval_types[1]:
            return (self.data.revenue[-1] / self.data.revenue[-2]) - 1

    def find_ebitda_as_percent(self):
        logging.debug(
            "calculating {} ebitda as percent of revenue...".format(self.eval_type)
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.data.ebitda)
        elif self.eval_type == eval_types[1]:
            return self.data.ebitda[-1] / self.data.revenue[-1]

    def find_dpn_as_percent(self):
        logging.debug(
            "calculating {} depreciation and amoritization as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.data.dpn_and_am)
        elif self.eval_type == eval_types[1]:
            return self.data.dpn_and_am[-1] / self.data.revenue[-1]

    def find_nwc_as_percent(self):
        logging.debug(
            "calculating {} net working capital as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.past_nwc)
        elif self.eval_type == eval_types[1]:
            return self.past_nwc[-1] / self.data.revenue[-1]

    def find_capex_as_percent(self):
        logging.debug(
            "calculating {} capital expenditures as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return -self.avg_pct_revenue(self.data.capex)
        elif self.eval_type == eval_types[1]:
            return -(self.data.capex[-1] / self.data.revenue[-1])

    def avg_pct_revenue(self, li):
        result = []
        for i, item in enumerate(li):
            result.append(item / self.data.revenue[i])
        return self.list_avg(result)

    def get_nwc(self):
        nwc1 = []
        nwc2 = []
        nwc3 = []
        for i in range(len(self.data.revenue)):
            nwc1.append(
                (self.data.tca[i] - self.data.cash_and_equiv[i])
                - (self.data.tcl[i] - self.data.short_term_debt[i])
            )
            nwc2.append(
                self.data.receivables[i]
                + self.data.inventories[i]
                - self.data.payables[i]
            )
            nwc3.append(self.data.tca[i] - self.data.tcl[i])
        if self.nwc_method == nwc_methods[0]:
            return self.data.dnwc
        elif self.nwc_method == nwc_methods[1]:
            return nwc1
        elif self.nwc_method == nwc_methods[2]:
            return nwc2
        elif self.nwc_method == nwc_methods[3]:
            return nwc3


class CashFlows(Margins):
    def __init__(
        self, eval_type, data_class, nwc_method, proj_years, custom=False, values=None
    ):
        super().__init__(
            eval_type, data_class, nwc_method, custom=custom, values=values
        )
        self.proj_years = proj_years
        self.years_list = self.make_years_list()
        self.old_fcf = self.past_fcf()
        self.zero_fcf = self.old_fcf[-1]
        self.proj_rev = self.find_proj_rev()
        self.proj_ebitda = self.find_projected(
            "ebitda as a percent of revenue", self.ebitda_pct_rev
        )
        self.proj_ebitda_after_tax = self.make_after_tax(self.proj_ebitda)
        self.proj_dpn = self.find_projected(
            "dpn as a percent of revenue", self.dpn_pct_rev
        )
        self.proj_dpn_shield = self.tax_shielder()
        self.proj_dnwc = self.find_proj_nwc()
        self.proj_capex = self.find_projected(
            "capex as a percent of revenue", self.capex_pct_rev
        )
        self.proj_fcf = self.find_future_fcf()

    def find_future_fcf(self):
        result = []
        for i, year in enumerate(self.proj_ebitda_after_tax):
            result.append(
                year + self.proj_dpn_shield[i] - self.proj_dnwc[i] - self.proj_capex[i]
            )
        return result

    def find_projected(self, value_name, percent_rev):
        logging.debug(
            "calculating projected {} over {} years based on {} average sales growth...".format(
                value_name, self.proj_years, self.eval_type
            )
        )
        result = []
        for year in self.proj_rev:
            result.append(year * percent_rev)
        return result

    def make_after_tax(self, li):
        result = []
        for year in li:
            result.append(year * (1 - self.tax_rate))
        return result

    def tax_shielder(self):
        result = []
        for year in self.proj_dpn:
            result.append(year * self.tax_rate)
        return result

    def find_proj_nwc(self):
        logging.debug(
            "calculating projected nwc as a percent of revenue over {} years based on {} average sales growth...".format(
                self.proj_years, self.eval_type
            )
        )
        rev = self.proj_rev
        rev.insert(0, self.data.revenue[-1])
        drev = []
        for i in range(len(rev) - 1):
            drev.append(rev[i + 1] - rev[i])
        result = []
        for year in drev:
            result.append(year * self.nwc_pct_rev)
        return result

    def find_proj_rev(self):
        logging.debug(
            "calculating projected revenue over {} years based on {} average sales growth...".format(
                self.proj_years, self.eval_type
            )
        )
        result = [self.data.revenue[-1] * (1 + self.sales_growth)]
        for i in range(len(self.years_list) - 1):
            result.append(result[i] * (1 + self.sales_growth))
        return result

    def past_fcf(self):
        logging.debug("calculating past free cash flows...")
        fcf = []
        for i in range(5):
            after_tax = 1 - self.data.tax_rates[i]
            ebitda_aft = self.data.ebitda[i] * after_tax
            dpn_shield = self.data.dpn_and_am[i] * self.data.tax_rates[i]
            fcf.append(ebitda_aft + dpn_shield - self.past_nwc[i] + self.data.capex[i])
        return fcf

    def make_years_list(self):
        li = []
        for i in range(self.proj_years):
            li.append(i + 1)
        return li


class Wacc(Functions):
    def __init__(self, eval_type, data_class, market_return, risk_free_rate):
        Functions.__init__(self, eval_type, data_class)
        self.data = data_class
        self.eval_type = eval_type
        self.market_return = self.as_percent(market_return)
        self.risk_free_rate = self.as_percent(risk_free_rate)
        self.debt = self.find_debt()
        logging.debug("calculating market value of equity...")
        self.market_equity = self.data.current_price["last"] * self.data.wavgshares[-1]
        logging.debug("calculating weight of equity...")
        self.we = self.market_equity / (self.market_equity + self.debt)
        logging.debug("calculating weight of debt...")
        self.wd = self.debt / (self.market_equity + self.debt)
        logging.debug("calculating the market rate premium...")
        self.mrp = self.market_return - self.risk_free_rate
        logging.debug("calculating the return on equity")
        self.re = self.risk_free_rate + (self.mrp * self.data.beta)
        logging.debug("calculating the interest rate of debt...")
        self.rd = self.find_rd()
        logging.debug("calculating weighted average cost of capital...")
        self.wacc = (self.re * self.we) + (self.rd * self.wd * (1 - self.tax_rate))

    def find_rd(self):
        if self.eval_type == eval_types[0]:
            return self.list_avg(self.data.interest_expense) / self.debt
        else:
            return self.data.interest_expense[-1] / self.debt

    def find_debt(self):
        logging.debug("calculating {} total debt...".format(self.eval_type))
        if self.eval_type == eval_types[0]:
            totals = []
            for i, year in enumerate(self.data.long_term_debt):
                totals.append(year + self.data.short_term_debt[i])
            return self.list_avg(totals)
        else:
            return self.data.long_term_debt[-1] + self.data.short_term_debt[-1]


class Evaluation(CashFlows, Wacc):
    def __init__(
        self,
        eval_type,
        data_class,
        market_return,
        risk_free_rate,
        nwc_method,
        proj_years,
        terminal_growth,
        custom=False,
        values=None,
    ):
        CashFlows.__init__(
            self,
            eval_type,
            data_class,
            nwc_method,
            proj_years,
            custom=custom,
            values=values,
        )
        Wacc.__init__(self, eval_type, data_class, market_return, risk_free_rate)
        self.npv = self.find_npv()
        self.terminal_growth = self.as_percent(terminal_growth)
        logging.debug(
            "calculating terminal value of future cash flows using {} values...".format(
                self.eval_type
            )
        )
        self.tv = self.proj_fcf[-1] / (self.wacc - self.terminal_growth)
        logging.debug(
            "calculating present value of terminal value using {} values...".format(
                self.eval_type
            )
        )
        self.pv_of_tv = self.tv / ((1 + self.wacc) ** (proj_years))
        logging.debug(
            "calculating enterprise value using {} values...".format(self.eval_type)
        )
        self.pv_of_eq = self.npv + self.pv_of_tv
        logging.debug(
            "calculating value of shareholder equity using {} values...".format(
                self.eval_type
            )
        )
        self.equity = self.find_equity()
        logging.info(
            "calculating fair price per share based on {} values".format(self.eval_type)
        )
        self.fair_price = self.equity / self.data.wavgshares[-1]
        self.warning = self.warning_text()

    def find_equity(self):
        logging.debug(
            "calculating shareholder equity using {} values".format(self.eval_type)
        )
        if self.eval_type == eval_types[0]:
            return self.pv_of_eq + self.list_avg(self.data.excess_cash) + self.debt
        else:
            return self.pv_of_eq + self.data.excess_cash[-1] + self.debt

    def find_npv(self):
        logging.debug(
            "calculating net present value fo future cash flows using {} values...".format(
                self.eval_type
            )
        )
        npv = self.zero_fcf
        for i, year in enumerate(self.proj_fcf):
            npv = npv + (year / ((1 - self.wacc) ** (i + 1)))
        return npv

    def display(self):
        return """
    Sales Growth: {0}
    Effective Tax Rate: {1}
    EBITDA as a Percent of Revenue: {2}
    Depreciation as a Percent of Revenue: {3}
    NWC as a Percent of Revenue: {4}
    CAPEX as a Percent of Revenue: {5}

    Estimated PV of Future FCFs: {6}
    Fair Price Per Share: {7}
    Last Price on {8}: {9}
        """.format(
            self.display_percent(self.sales_growth),
            self.display_percent(self.tax_rate),
            self.display_percent(self.ebitda_pct_rev),
            self.display_percent(self.dpn_pct_rev),
            self.display_percent(self.nwc_pct_rev),
            self.display_percent(self.capex_pct_rev),
            self.display_million(self.equity),
            self.display_dollars(self.fair_price),
            self.data.current_price["date"],
            self.display_dollars(self.data.current_price["last"]),
        )

    def assessment(self):
        # TODO Fix assessment to look nicer
        pct_diff = (
            (self.fair_price - self.data.current_price["last"])
            / self.data.current_price["last"]
        ) - 1
        if pct_diff < -0.1:
            under_over = "OVER"
        elif pct_diff > 0.1:
            under_over = "UNDER"
        else:
            under_over = "FAIRLY"
            return (
                "{} VALUED".format(under_over),
                self.display_percent(pct_diff),
                self.display_dollars(self.fair_price - self.data.current_price["last"]),
            )
        if abs(pct_diff) > abs(0.4):
            degree = "HIGHLY"
        else:
            degree = "MODERATELY"
        return (
            "{} {} VALUED".format(degree, under_over),
            self.display_percent(pct_diff),
            self.display_dollars(self.fair_price - self.data.current_price["last"]),
        )

    def excel_data(self):
        pass

    @staticmethod
    def warning_text():
        return """Warning:
stock assessment and evaluations can vary
drasitcally based on the inputs and 
no financial transctions should be made without
verification of the accuracy of the inputs provided.
additionally, it is recommended that the evaluation be
saved in excel format for further consideration"""
