#! python3
"""
evaluation.py - Discounted Cash Flow (DCF) valuation engine for AutoValu.

Implements a multi-layer class hierarchy that progressively builds a full DCF
model from raw financial data.

Classes:
    Functions: Base utility class providing shared financial math helpers.
    Margins: Computes revenue-relative margin percentages used in projections.
    CashFlows: Projects future free cash flows based on margin assumptions.
    Wacc: Calculates the Weighted Average Cost of Capital (WACC).
    Evaluation: Combines CashFlows and Wacc to produce a fair value per share.

Variables:
    eval_types (tuple[str, ...]): Supported evaluation modes: 'Historical', 'Recent', 'Custom'.
    nwc_methods (tuple[str, ...]): Supported NWC calculation methods.
"""

import logging
from typing import TYPE_CHECKING, Optional

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

if TYPE_CHECKING:
    from modules.api import DataValues

eval_types = ("Historical", "Recent", "Custom")
nwc_methods = (
    "As Reported",
    "(TCA-Cash)-(TCL-Debt)",
    "(A/R+Inventories-A/P)",
    "(TCA-TCL)",
)


class Functions:
    """Base utility class providing shared financial math and display helpers.

    Methods:
        __init__: Compute and store the effective tax rate for this evaluation.
        find_tax_rate: Select the tax rate based on evaluation type.
        as_percent: Convert a whole-number percentage to a decimal.
        list_avg: Compute the arithmetic mean of a list of numbers.
        display_percent: Format a decimal as a percentage string.
        display_dollars: Format a number as a dollar string.
        display_million: Format a number as a dollar-millions string.
    """

    def __init__(
        self,
        eval_type: str,
        data_class: "DataValues",
        custom: bool = False,
        values: Optional[dict] = None,
    ) -> None:
        """Compute and store the effective tax rate for this evaluation.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.
            custom (bool): If True, tax rate is taken from values rather than computed.
            values (dict | None): Custom margin overrides keyed by metric name.
        """
        if custom:
            self.tax_rate = self.as_percent(values["tax rate"])
        else:
            self.tax_rate = self.find_tax_rate(eval_type, data_class)

    def find_tax_rate(self, eval_type: str, data_class: "DataValues") -> float:
        """Select the effective tax rate based on evaluation type.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.

        Returns:
            float: Historical 5-year average tax rate, or the most recent year's rate.
        """
        logging.debug("calculating {} effective tax rate".format(eval_type))
        if eval_type == eval_types[0]:
            return self.list_avg(data_class.tax_rates)
        else:
            return data_class.tax_rates[-1]

    @staticmethod
    def as_percent(number: float) -> float:
        """Convert a whole-number percentage to a decimal fraction."""
        percent = number / 100
        return percent

    @staticmethod
    def list_avg(li: list | tuple) -> float:
        """Compute the arithmetic mean of a sequence of numbers."""
        total = 0
        for i in li:
            total += i
        return total / len(li)

    @staticmethod
    def display_percent(decimal: float) -> str:
        """Format a decimal fraction as a rounded percentage string."""
        return "{}%".format(round(decimal * 100, 2))

    @staticmethod
    def display_dollars(amount: float) -> str:
        """Format a number as a dollar string rounded to two decimal places."""
        return "${}".format(round(amount, 2))

    @staticmethod
    def display_million(amount: float) -> str:
        """Format a number as a dollar-millions string rounded to two decimal places."""
        return "${}M".format(round(amount / 10 ** 6, 2))


class Margins(Functions):
    """Computes revenue-relative margin percentages used to project future cash flows.

    Attributes:
        eval_type (str): Evaluation mode used for this instance.
        data (DataValues): Parsed financial data for the target company.
        nwc_method (str): NWC calculation method selected by the user.
        sales_growth (float): Projected sales growth rate as a decimal.
        ebitda_pct_rev (float): EBITDA as a percentage of revenue.
        dpn_pct_rev (float): Depreciation & amortization as a percentage of revenue.
        past_nwc (list | tuple): Historical net working capital values.
        nwc_pct_rev (float): NWC as a percentage of revenue.
        capex_pct_rev (float): Capital expenditures as a percentage of revenue.

    Methods:
        __init__: Compute all margin percentages for this evaluation.
        find_sales_growth: Compute projected sales growth rate.
        find_ebitda_as_percent: Compute EBITDA as a percentage of revenue.
        find_dpn_as_percent: Compute D&A as a percentage of revenue.
        find_nwc_as_percent:  Compute NWC as a percentage of revenue.
        find_capex_as_percent: Compute CapEx as a percentage of revenue.
        avg_pct_revenue: Compute the average of a metric as a percentage of revenue.
        get_nwc: Return historical NWC values using the selected method.
    """

    def __init__(
        self,
        eval_type: str,
        data_class: "DataValues",
        nwc_method: str,
        custom: bool = False,
        values: Optional[dict] = None,
    ) -> None:
        """Compute all margin percentages for this evaluation.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.
            nwc_method (str): NWC calculation method — one of nwc_methods.
            custom (bool): If True, margins are overridden with values from values dict.
            values (dict | None): Custom margin overrides keyed by metric name.
        """
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

    def find_sales_growth(self) -> float:
        """Compute the projected sales growth rate.

        Returns:
            float: Historical average or most-recent year-over-year revenue growth as a decimal.
        """
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

    def find_ebitda_as_percent(self) -> float:
        """Compute EBITDA as a percentage of revenue.

        Returns:
            float: Historical average or most-recent EBITDA margin as a decimal.
        """
        logging.debug(
            "calculating {} ebitda as percent of revenue...".format(self.eval_type)
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.data.ebitda)
        elif self.eval_type == eval_types[1]:
            return self.data.ebitda[-1] / self.data.revenue[-1]

    def find_dpn_as_percent(self) -> float:
        """Compute depreciation & amortization as a percentage of revenue.

        Returns:
            float: Historical average or most-recent D&A margin as a decimal.
        """
        logging.debug(
            "calculating {} depreciation and amoritization as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.data.dpn_and_am)
        elif self.eval_type == eval_types[1]:
            return self.data.dpn_and_am[-1] / self.data.revenue[-1]

    def find_nwc_as_percent(self) -> float:
        """Compute net working capital as a percentage of revenue.

        Returns:
            float: Historical average or most-recent NWC margin as a decimal.
        """
        logging.debug(
            "calculating {} net working capital as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return self.avg_pct_revenue(self.past_nwc)
        elif self.eval_type == eval_types[1]:
            return self.past_nwc[-1] / self.data.revenue[-1]

    def find_capex_as_percent(self) -> float:
        """Compute capital expenditures as a percentage of revenue.

        Returns:
            float: Historical average or most-recent CapEx margin as a decimal (positive).
        """
        logging.debug(
            "calculating {} capital expenditures as percent of revenue...".format(
                self.eval_type
            )
        )
        if self.eval_type == eval_types[0]:
            return -self.avg_pct_revenue(self.data.capex)
        elif self.eval_type == eval_types[1]:
            return -(self.data.capex[-1] / self.data.revenue[-1])

    def avg_pct_revenue(self, li: list | tuple) -> float:
        """Compute the average of a financial metric expressed as a percentage of revenue.

        Args:
            li (list | tuple): Historical values of the metric, aligned by year with revenue.

        Returns:
            float: Average metric-to-revenue ratio across all years.
        """
        result = []
        for i, item in enumerate(li):
            result.append(item / self.data.revenue[i])
        return self.list_avg(result)

    def get_nwc(self) -> list | tuple:
        """Return historical NWC values using the method selected by the user.

        Returns:
            list | tuple: Historical NWC values, one per fiscal year, calculated
                          according to self.nwc_method.
        """
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
    """Projects future free cash flows over the user-specified forecast period.

    Attributes:
        proj_years (int): Number of years to project cash flows.
        years_list (list[int]): Ordered list of forecast year indices.
        old_fcf (list[float]): Historical free cash flows over the past 5 years.
        zero_fcf (float): Most recent historical FCF, used as the NPV starting value.
        proj_rev (list[float]): Projected revenues for each forecast year.
        proj_ebitda (list[float]): Projected EBITDA for each forecast year.
        proj_ebitda_after_tax (list[float]): After-tax projected EBITDA.
        proj_dpn (list[float]): Projected D&A for each forecast year.
        proj_dpn_shield (list[float]): Tax shield from projected D&A.
        proj_dnwc (list[float]): Projected change in NWC for each forecast year.
        proj_capex (list[float]): Projected CapEx for each forecast year.
        proj_fcf (list[float]): Projected free cash flows for each forecast year.

    Methods:
        __init__: Compute all projected cash flow components.
        find_future_fcf: Assemble projected FCF from component projections.
        find_projected: Project a metric over the forecast period using percent-of-revenue.
        make_after_tax: Apply the effective tax rate to a list of EBITDA values.
        tax_shielder: Compute the D&A tax shield for each forecast year.
        find_proj_nwc: Project the change in NWC for each forecast year.
        find_proj_rev: Project revenue for each forecast year.
        past_fcf: Calculate historical FCF for the past 5 years.
        make_years_list: Build the ordered list of forecast year indices.
    """

    def __init__(
        self,
        eval_type: str,
        data_class: "DataValues",
        nwc_method: str,
        proj_years: int,
        custom: bool = False,
        values: Optional[dict] = None,
    ) -> None:
        """Compute all projected cash flow components over the forecast period.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.
            nwc_method (str): NWC calculation method — one of nwc_methods.
            proj_years (int): Number of years to project cash flows.
            custom (bool): If True, margin assumptions are taken from values.
            values (dict | None): Custom margin overrides keyed by metric name.
        """
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

    def find_future_fcf(self) -> list[float]:
        """Assemble projected free cash flows from their component projections.

        Returns:
            list[float]: Projected FCF for each year in the forecast period.
        """
        result = []
        for i, year in enumerate(self.proj_ebitda_after_tax):
            result.append(
                year + self.proj_dpn_shield[i] - self.proj_dnwc[i] - self.proj_capex[i]
            )
        return result

    def find_projected(self, value_name: str, percent_rev: float) -> list[float]:
        """Project a financial metric over the forecast period using percent-of-revenue.

        Args:
            value_name (str): Descriptive name of the metric (used for logging).
            percent_rev (float): The metric expressed as a decimal fraction of revenue.

        Returns:
            list[float]: Projected metric values for each year in the forecast period.
        """
        logging.debug(
            "calculating projected {} over {} years based on {} average sales growth...".format(
                value_name, self.proj_years, self.eval_type
            )
        )
        result = []
        for year in self.proj_rev:
            result.append(year * percent_rev)
        return result

    def make_after_tax(self, li: list[float]) -> list[float]:
        """Apply the effective tax rate to reduce a list of pre-tax values.

        Args:
            li (list[float]): Pre-tax values for each forecast year.

        Returns:
            list[float]: After-tax values for each forecast year.
        """
        result = []
        for year in li:
            result.append(year * (1 - self.tax_rate))
        return result

    def tax_shielder(self) -> list[float]:
        """Compute the D&A tax shield for each forecast year.

        Returns:
            list[float]: Tax shield amounts (D&A * tax_rate) for each forecast year.
        """
        result = []
        for year in self.proj_dpn:
            result.append(year * self.tax_rate)
        return result

    def find_proj_nwc(self) -> list[float]:
        """Project the change in net working capital for each forecast year.

        Returns:
            list[float]: Projected delta-NWC for each year in the forecast period.
        """
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

    def find_proj_rev(self) -> list[float]:
        """Project revenue for each year in the forecast period.

        Returns:
            list[float]: Projected revenue for each year, compounded from the most
                         recent fiscal year using the estimated sales growth rate.
        """
        logging.debug(
            "calculating projected revenue over {} years based on {} average sales growth...".format(
                self.proj_years, self.eval_type
            )
        )
        result = [self.data.revenue[-1] * (1 + self.sales_growth)]
        for i in range(len(self.years_list) - 1):
            result.append(result[i] * (1 + self.sales_growth))
        return result

    def past_fcf(self) -> list[float]:
        """Calculate historical free cash flow for each of the past 5 fiscal years.

        Returns:
            list[float]: Historical FCF values ordered from oldest to most recent.
        """
        logging.debug("calculating past free cash flows...")
        fcf = []
        for i in range(5):
            after_tax = 1 - self.data.tax_rates[i]
            ebitda_aft = self.data.ebitda[i] * after_tax
            dpn_shield = self.data.dpn_and_am[i] * self.data.tax_rates[i]
            fcf.append(ebitda_aft + dpn_shield - self.past_nwc[i] + self.data.capex[i])
        return fcf

    def make_years_list(self) -> list[int]:
        """Build the ordered list of forecast year indices starting at 1.

        Returns:
            list[int]: List [1, 2, ..., proj_years].
        """
        li = []
        for i in range(self.proj_years):
            li.append(i + 1)
        return li


class Wacc(Functions):
    """Calculates the Weighted Average Cost of Capital (WACC).

    Attributes:
        data (DataValues): Parsed financial data for the target company.
        eval_type (str): Evaluation mode used for this instance.
        market_return (float): Expected market rate of return as a decimal.
        risk_free_rate (float): Risk-free rate of return as a decimal.
        debt (float): Total debt (long-term + short-term) in dollars.
        market_equity (float): Market value of equity (price × diluted shares) in dollars.
        we (float): Weight of equity in the capital structure.
        wd (float): Weight of debt in the capital structure.
        mrp (float): Market risk premium (market_return - risk_free_rate).
        re (float): Required return on equity via CAPM.
        rd (float): Average interest rate on debt.
        wacc (float): Weighted Average Cost of Capital as a decimal.

    Methods:
        __init__: Compute all WACC components.
        find_rd: Compute the average interest rate on debt.
        find_debt: Compute total debt used in the capital structure weighting.
    """

    def __init__(
        self,
        eval_type: str,
        data_class: "DataValues",
        market_return: float,
        risk_free_rate: float,
    ) -> None:
        """Compute all WACC components for this evaluation.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.
            market_return (float): Expected market rate of return as a whole number (e.g. 10 for 10%).
            risk_free_rate (float): Risk-free rate of return as a whole number (e.g. 4 for 4%).
        """
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

    def find_rd(self) -> float:
        """Compute the average interest rate on debt (interest expense / total debt).

        Returns:
            float: Historical average or most-recent cost of debt as a decimal.
        """
        if self.eval_type == eval_types[0]:
            return self.list_avg(self.data.interest_expense) / self.debt
        else:
            return self.data.interest_expense[-1] / self.debt

    def find_debt(self) -> float:
        """Compute total debt used in the capital structure weighting.

        Returns:
            float: Historical average or most-recent total debt (long-term + short-term) in dollars.
        """
        logging.debug("calculating {} total debt...".format(self.eval_type))
        if self.eval_type == eval_types[0]:
            totals = []
            for i, year in enumerate(self.data.long_term_debt):
                totals.append(year + self.data.short_term_debt[i])
            return self.list_avg(totals)
        else:
            return self.data.long_term_debt[-1] + self.data.short_term_debt[-1]


class Evaluation(CashFlows, Wacc):
    """Combines projected cash flows and WACC to produce a DCF fair value per share.

    Attributes:
        npv (float): Net present value of projected free cash flows.
        terminal_growth (float): Perpetual growth rate beyond the forecast period as a decimal.
        tv (float): Terminal value of cash flows beyond the forecast period.
        pv_of_tv (float): Present value of the terminal value.
        pv_of_eq (float): Enterprise value (NPV + PV of terminal value).
        equity (float): Total shareholder equity value after adjustments.
        fair_price (float): Estimated fair price per share in dollars.
        warning (str): Standard disclaimer text for all evaluations.

    Methods:
        __init__: Run the full DCF calculation and store all results.
        find_equity: Compute total shareholder equity from enterprise value.
        find_npv: Compute the net present value of projected free cash flows.
        display: Return a formatted summary string of key evaluation metrics.
        assessment: Return an under/over valuation verdict tuple.
        excel_data: Placeholder for future Excel data export logic.
        warning_text: Return the standard evaluation disclaimer text (static).
    """

    def __init__(
        self,
        eval_type: str,
        data_class: "DataValues",
        market_return: float,
        risk_free_rate: float,
        nwc_method: str,
        proj_years: int,
        terminal_growth: float,
        custom: bool = False,
        values: Optional[dict] = None,
    ) -> None:
        """Run the full DCF calculation and store all results.

        Args:
            eval_type (str): Evaluation mode — one of eval_types.
            data_class (DataValues): Parsed financial data for the target company.
            market_return (float): Expected market rate of return as a whole number (e.g. 10).
            risk_free_rate (float): Risk-free rate of return as a whole number (e.g. 4).
            nwc_method (str): NWC calculation method — one of nwc_methods.
            proj_years (int): Number of years to project cash flows.
            terminal_growth (float): Perpetual growth rate beyond the forecast period as a whole number.
            custom (bool): If True, margin assumptions are taken from values.
            values (dict | None): Custom margin overrides keyed by metric name.
        """
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

    def find_equity(self) -> float:
        """
        Compute total shareholder equity value from enterprise value.
        Adds excess cash and debt back to the present value of equity, consistent
        with standard DCF equity bridge methodology.

        Returns:
            float: Total equity value in dollars.
        """
        logging.debug(
            "calculating shareholder equity using {} values".format(self.eval_type)
        )
        if self.eval_type == eval_types[0]:
            return self.pv_of_eq + self.list_avg(self.data.excess_cash) + self.debt
        else:
            return self.pv_of_eq + self.data.excess_cash[-1] + self.debt

    def find_npv(self) -> float:
        """Compute the net present value of projected free cash flows.

        Returns:
            float: NPV of the forecast period cash flows, discounted at WACC.
        """
        logging.debug(
            "calculating net present value fo future cash flows using {} values...".format(
                self.eval_type
            )
        )
        npv = self.zero_fcf
        for i, year in enumerate(self.proj_fcf):
            npv = npv + (year / ((1 - self.wacc) ** (i + 1)))
        return npv

    def display(self) -> str:
        """Return a formatted multi-line summary of key evaluation metrics."""
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

    def assessment(self) -> tuple[str, str, str]:
        """Return an under/over valuation verdict based on the fair price vs current price.

        Returns:
            tuple[str, str, str]: A three-element tuple of
                (valuation label, percent difference string, dollar difference string).
        """
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

    def excel_data(self) -> None:
        """Placeholder for future Excel data export logic."""
        pass

    @staticmethod
    def warning_text() -> str:
        """Return the standard evaluation disclaimer text."""
        return """Warning:
stock assessment and evaluations can vary
drasitcally based on the inputs and
no financial transctions should be made without
verification of the accuracy of the inputs provided.
additionally, it is recommended that the evaluation be
saved in excel format for further consideration"""
