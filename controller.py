#! python3
"""
controller.py - MVC controller for AutoValu.

Mediates between the PyQt5 view and the backend model, handling page navigation,
API/database caching decisions, user input validation, and evaluation orchestration.

Classes:
    Controller: Main application controller and entry point.
"""

import logging
import sys
from typing import TYPE_CHECKING, Optional, Any

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)

from PyQt5 import QtCore, QtWidgets
from view import Ui_View, QtGui
from model import Model

if TYPE_CHECKING:
    from modules.evaluation import Evaluation


class Controller:
    """Main application controller that wires together the view and the model.

    Attributes:
        pages (dict): Maps page class names to their current rendered widget instances.
        page_history (list): Ordered history of rendered/shown page widget instances.
        model (Model): Backend model facade providing access to all modules.
        api_obj (APIData): Active APIData instance used for all API calls.
        view (Ui_View): Main application window and stacked widget container.
        nwc_methods (tuple[str, ...]): Available NWC calculation method labels.
        eval_types (tuple[str, ...]): Available evaluation type labels.
        data_access_time (str | None): Timestamp key used to load a cached evaluation,
            or None when a fresh API call is needed.
        load (bool): True when displaying history results rather than live search results.
        search_results (list | None): Most recent autocomplete or history search results.
        chosen_company (dict): Identifier fields for the company selected by the user.
        inputs (dict | None): Validated DCF model parameters collected from InputPage.
        company_profile (dict | None): Profile data for the currently selected company.
        company_data (DataValues | None): Parsed financial data for the current evaluation.
        evaluations (list[Evaluation]): The three Evaluation instances produced per run
            in order: Custom, Recent, Historical.

    Methods:
        __init__: Initialize the model, view, and launch the application.
        load_frame: Gather required data and render a new page onto the stack.
        send_search: Submit a search query and display autocomplete results.
        search_history: Load and display all previously stored evaluations.
        update_company_profile: Fetch or load the profile for the selected company.
        update_inputs: Validate and store user-supplied DCF parameters.
        update_company_data: Fetch or load all financial data for the selected company.
        create_evaluations: Run Historical, Recent, and Custom DCF evaluations.
        render_frame: Instantiate a page class and push it onto the stacked widget.
        show_frame: Switch the stacked widget to an already-rendered page.
        find_last_page: Return the second-to-last page in the navigation history.
        back_button: Navigate to the previous page in history.
        save_button: Open a save dialog and export the evaluations to Excel.
        input_error: Validate and coerce raw string inputs to their target types.
        get_treeview_row: Populate chosen_company from a selected tree view row.
        find_expected_return: Open the expected market return reference page.
        find_risk_free_rate: Open the risk-free rate reference page.
        eval_avg: Compute the average of Historical and Recent margin assumptions (static).
        exit_app: Terminate the application (static).
    """

    def __init__(self) -> None:
        """Initialize the model, view, and all application state, then launch the UI."""
        # initialize view and model
        self.pages = {}
        self.page_history = []
        self.model = Model()
        self.api_obj = self.model.find()
        self.view = Ui_View(self)

        # define possible choices for evaluations
        self.nwc_methods = (
            "As Reported",
            "(TCA-Cash)-(TCL-Debt)",
            "(A/R+Inventories-A/P)",
            "(TCA-TCL)",
        )
        self.eval_types = ("Historical", "Recent", "Custom")

        # define variable to determine if db or api is queried
        self.data_access_time: Optional[str] = None
        self.load: bool = False
        self.search_results: Optional[list] = None

        # render search page to start app
        self.view.show_ui()

    ###   Page Changers   ###
    def load_frame(self, page: type[QtWidgets.QWidget], inputs: Optional[dict] = None) -> None:
        """
        Gather required data and render a new page onto the stacked widget.

        Behaviour varies by page:
        - search_page: resets the chosen company and renders immediately.
        - input_page: validates a company is selected, then fetches its profile.
        - summary_page: validates inputs, fetches financial data, runs evaluations.

        Args:
            page (type[QWidget]): The page class to instantiate and display.
            inputs (dict | None): Raw input values from InputPage, required when
                navigating to summary_page.
        """
        ## types of information gathered based on page to load
        if page == self.view.search_page:
            self.chosen_company = {}
            self.render_frame(page)
            logging.info("login successful")

        # render input page #
        # TODO add load option
        elif page == self.view.input_page:
            self.inputs = None
            if self.chosen_company == {}:
                self.view.error("Please select a company before proceeding")
                return
            else:
                self.render_frame(page)
                self.update_company_profile()

        # render summary page #
        # TODO add load option
        elif page == self.view.summary_page:
            self.company_data = None
            errors = self.update_inputs(inputs)
            if self.inputs == None:
                self.view.error(errors)
                return
            self.update_company_data()
            self.create_evaluations(self.inputs)
            self.render_frame(page)
            self.pages[self.view.summary_page.__name__].update_labels(
                self.evaluations[0].assessment()
            )

    ###   View Model Interactions   ###
    def send_search(self, query: str) -> None:
        """
        Submit a search query and display autocomplete results in the search table.

        Checks the database cache first; falls back to a live API call if the
        query has not been seen before.

        Args:
            query (str): The search text entered by the user.
        """
        if query == "":
            self.view.error("Please enter a search into the search bar")
            return
        logging.info("search query : {}".format(query))

        # --- DEMO: The Morningstar API no longer exists. The block below (commented out)
        # --- originally checked the DB cache and fell back to a live API call.
        # --- It is preserved here for reference.
        #
        # self.load = False
        # in_db = self.model.db.load_searches(query)
        # if in_db == None:
        #     try:
        #         self.search_results = self.api_obj.auto_complete_call(query)
        #     except Exception:
        #         self.view.error("Could not reach the API.")
        #         return
        #     self.model.db.make_search_inst(query, self.search_results)
        # else:
        #     self.api_obj.search_results = in_db
        #     self.search_results = in_db
        #
        # if len(self.search_results) == 0:
        #     self.view.error(
        #         "No search results found for {}\nPlease try another search".format(query)
        #     )
        #     return
        # self.pages[self.view.search_page.__name__].display_search_results(
        #     self.search_results
        # )
        # logging.debug("search_results : {}".format(self.search_results))

        # --- DEMO: Forcibly load all stored evaluations from the local database and
        # --- display them in the search table regardless of what was searched.
        # --- Run seed_db.py first to populate the database with Apple (AAPL) data.
        history = self.model.db.all_past_inst()
        if not history:
            self.view.error(
                "No demo data found. Please run seed_db.py to populate the database."
            )
            return
        self.load = True
        self.search_results = [record[1] for record in history]
        time_stamps = [record[0] for record in history]
        self.pages[self.view.search_page.__name__].display_search_results(
            self.search_results, time_stamps=time_stamps
        )
        logging.debug("search_results (demo) : {}".format(self.search_results))

    def search_history(self, query: str) -> None:
        """
        Load and display all previously stored evaluations in the search table.

        Args:
            query (str): Unused; present for interface consistency with send_search.
        """
        logging.info("loading past evaluations")
        self.load = True
        search_history = self.model.db.all_past_inst()
        search_results = []
        time_stamps = []
        for result in search_history:
            search_results.append(result[1])
            time_stamps.append(result[0])
        self.pages[self.view.search_page.__name__].display_search_results(
            search_results, time_stamps=time_stamps
        )
        logging.debug("search_history : {}".format(search_results))

    def update_company_profile(self) -> None:
        """
        Fetch or load the company profile for the currently selected company.
        Checks the database cache first; falls back to a live API call if the
        profile for this security ID has not been stored before.
        """
        in_db = self.model.db.load_profile(self.chosen_company["securityId"])
        if in_db == None:
            # --- DEMO: The profile for this company is not in the local database.
            # --- The original API call that would fetch it is no longer available.
            # --- Original code (preserved for reference):
            # try:
            #     self.company_profile = self.api_obj.company_profile_call(
            #         self.chosen_company["mic"], self.chosen_company["ticker"]
            #     )
            # except Exception:
            #     self.view.error("Could not fetch company profile.")
            #     return
            # self.model.db.make_profile_inst(
            #     self.chosen_company["securityId"], self.company_profile
            # )
            self.view.error("Profile not in database. Please run seed_db.py first.")
            return
        else:
            self.api_obj.company_profile = in_db
            self.company_profile = in_db
        self.pages[self.view.input_page.__name__].update_labels(self.company_profile)
        logging.debug("company profile collected : {}".format(self.company_profile))

    def update_inputs(self, inputs: dict[str, tuple]) -> str | dict:
        """
        Validate and coerce raw string inputs to their target types.
        Delegates to input_error and stores the validated result in self.inputs.
        If validation fails, self.inputs remains None and an error string is returned.

        Args:
            inputs (dict[str, tuple]): Mapping of parameter name to
                (raw_string_value, target_type) pairs from InputPage.get_inputs().

        Returns:
            str | dict: Error message string if any input fails conversion,
                        otherwise the validated parameter dict.
        """
        inputs, errors = self.input_error(self.view.input_page, inputs)
        if len(errors) > 0:
            err_msg = ""
            for error in errors:
                err_msg = err_msg + "{} value '{}' can not be converted to {}\n".format(
                    error[0], error[1], error[2].__name__
                )
            return err_msg
        else:
            self.inputs = inputs
            return inputs

    def update_company_data(self) -> None:
        """
        Fetch or load all financial data for the currently selected company.
        Uses data_access_time to look up a cached record; if none exists,
        queries the Morningstar API and stores the result in the database.
        """
        in_db = self.model.db.load_data(self.data_access_time)
        if in_db == None:
            # --- DEMO: Financial data for this timestamp is not cached locally.
            # --- The original API call that would fetch it is no longer available.
            # --- Original code (preserved for reference):
            # try:
            #     self.api_obj.query_morningstar(self.chosen_company)
            # except Exception:
            #     self.view.error("Could not fetch financial data.")
            #     return
            # self.company_data = self.model.gather(
            #     self.chosen_company, self.api_obj.data_object()
            # )
            # self.model.db.make_data_inst(
            #     self.chosen_company, self.api_obj.data_object(), self.inputs
            # )
            self.view.error("Data not in database. Please run seed_db.py first.")
            return
        else:
            data = in_db["company_data"]
            self.company_data = self.model.gather(self.chosen_company, data)

    def create_evaluations(self, inputs: dict) -> None:
        """
        Run Historical, Recent, and Custom DCF evaluations for the current company.
        Populates self.evaluations with three Evaluation instances in the order
        [Custom, Recent, Historical]. Custom assumptions are the average of
        Historical and Recent margin values.

        Args:
            inputs (dict): Validated DCF parameters from update_inputs, containing
                'market_return', 'risk_free_rate', 'nwc_method', 'proj_years',
                and 'terminal_growth'.
        """
        self.evaluations = []
        self.evaluations.append(
            self.model.evaluate(
                self.eval_types[0],
                self.company_data,
                inputs["market_return"],
                inputs["risk_free_rate"],
                inputs["nwc_method"],
                inputs["proj_years"],
                inputs["terminal_growth"],
            )
        )
        self.evaluations.insert(
            0,
            self.model.evaluate(
                self.eval_types[1],
                self.company_data,
                inputs["market_return"],
                inputs["risk_free_rate"],
                inputs["nwc_method"],
                inputs["proj_years"],
                inputs["terminal_growth"],
            ),
        )
        self.evaluations.insert(
            0,
            self.model.evaluate(
                self.eval_types[2],
                self.company_data,
                inputs["market_return"],
                inputs["risk_free_rate"],
                inputs["nwc_method"],
                inputs["proj_years"],
                inputs["terminal_growth"],
                custom=True,
                values=self.eval_avg(self.evaluations[0], self.evaluations[1]),
            ),
        )

    ###   View Controllers   ###
    def render_frame(self, page: type[QtWidgets.QWidget]) -> None:
        """
        Instantiate a page class and push it onto the stacked widget.
        Always creates a fresh instance of the page to ensure displayed data
        is current. The new widget is added to the stack and made active.

        Args:
            page (type[QWidget]): The page class to instantiate and display.
        """
        # run or Rerun code for new page to ensure current data displayed
        self.pages[page.__name__] = page(self)
        new_page = self.pages[page.__name__]
        self.view.stackedWidget.addWidget(new_page)
        self.view.stackedWidget.setCurrentWidget(new_page)
        self.page_history.append(new_page)
        logging.debug("widget {} rendered".format(new_page.objectName()))

    def show_frame(self, page: type[QtWidgets.QWidget]) -> None:
        """
        Switch the stacked widget to an already-rendered page without rebuilding it.
        Args:
            page (type[QWidget]): The page class whose existing instance to display.
        """
        # show page that is already rendered
        try:
            new = self.page_history[-1] == self.pages[self.view.summary_page.__name__]
        except Exception:
            new = False
        if (page == self.view.search_page) and new:
            self.chosen_company = {}
        self.view.stackedWidget.setCurrentWidget(self.pages[page.__name__])
        self.page_history.append(self.pages[page.__name__])
        logging.debug("widget {} shown".format(self.pages[page.__name__].objectName()))

    def find_last_page(self) -> QtWidgets.QWidget:
        """
        Return the second-to-last page in the navigation history.
        Returns:
            QWidget: The previous page widget, skipping the AboutPage if it is current.
        """
        self.last_page = self.page_history[-2]
        if self.last_page == self.view.about_page:
            self.last_page = self.page_history[-1]
        return self.last_page

    ###   Unique Buttons   ###
    def back_button(self) -> None:
        """Navigate to the previous page in history, skipping the AboutPage."""
        last_page = self.page_history[-2]
        if last_page == self.pages[self.view.about_page.__name__]:
            last_page = self.page_history[-1]
        self.view.stackedWidget.setCurrentWidget(last_page)

    def save_button(self, parent: QtWidgets.QWidget) -> None:
        """Open a save-file dialog and export all three evaluations to the chosen path.

        Args:
            parent (QWidget): Parent widget for the file dialog.
        """
        files = """Excel File (*.xlsx);;
             CSV File (*.csv);;
             Python Files '*.py',
             Text Document (*.txt);;
             All Files (*.*)"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent, "Save Evaluation", "", files
        )
        logging.debug("save file path selected {}".format(filename))
        self.model.make_wb(self.evaluations, filename)

    ###   Error Controllers   ###
    def input_error(
        self, page: type[QtWidgets.QWidget], inputs: dict[str, tuple]
    ) -> tuple[dict, list]:
        """
        Validate and coerce raw string inputs to their declared target types.

        Args:
            page (type[QWidget]): The page class the inputs originated from
                (used for logging context).
            inputs (dict[str, tuple]): Mapping of parameter name to
                (raw_string_value, target_type) pairs.

        Returns:
            tuple[dict, list]: A two-element tuple of (validated_inputs, errors) where
                validated_inputs maps parameter names to coerced values and errors is
                a list of (name, raw_value, target_type) triples for each failed conversion.
        """
        errors = []
        to_model = {}
        for key in inputs.keys():
            value = inputs[key][0]
            typ = inputs[key][1]
            try:
                to_model[key] = typ(value)
            except ValueError:
                errors.append((key, str(value), typ))
                logging.error("could not convert {} to type {}".format(value, typ))
        logging.debug(
            "errors found in {} : {}".format(
                self.pages[page.__name__].objectName(), errors
            )
        )
        logging.debug(
            "inputs accepted from {} : {}".format(
                self.pages[page.__name__].objectName(), to_model
            )
        )
        return to_model, errors

    ###   Value Gatherers   ###
    def get_treeview_row(self, index: QtCore.QModelIndex) -> None:
        """
        Populate chosen_company from the row selected in the search results tree view.

        Args:
            index (QModelIndex): The model index of the double-clicked cell.
        """
        self.chosen_company["companyName"] = index.siblingAtColumn(0).data()
        self.chosen_company["ticker"] = index.siblingAtColumn(1).data()
        self.chosen_company["mic"] = index.siblingAtColumn(2).data()
        self.chosen_company["currency"] = index.siblingAtColumn(3).data()
        self.chosen_company["securityId"] = index.siblingAtColumn(4).data()
        self.chosen_company["endOfDayQuoteTicker"] = index.siblingAtColumn(5).data()
        self.data_access_time = index.siblingAtColumn(6).data()
        logging.info("results selected from treeview : {}".format(self.chosen_company))

    def find_expected_return(self) -> None:
        """Open the Market Risk Premia reference page in the default browser."""
        self.model.find.find_expected_return()

    def find_risk_free_rate(self) -> None:
        """Open the US Treasury yield reference page in the default browser."""
        self.model.find.find_risk_free()

    ###   Other Methods   ###
    @staticmethod
    def eval_avg(eval1: "Evaluation", eval2: "Evaluation") -> dict[str, float]:
        """Compute the average of Historical and Recent margin assumptions.

        Used to seed the Custom evaluation with blended assumptions.

        Args:
            eval1 (Evaluation): The first evaluation (Recent).
            eval2 (Evaluation): The second evaluation (Historical).

        Returns:
            dict[str, float]: Averaged margin assumptions as whole-number percentages,
                keyed by 'sales growth', 'ebitda', 'dpn', 'tax rate', 'nwc', and 'capex'.
        """
        def as_whole_num(num: float) -> float:
            return num * 100

        def average(val1: float, val2: float) -> float:
            return (val1 + val2) / 2

        avg = {
            "sales growth": average(
                as_whole_num(eval1.sales_growth), as_whole_num(eval2.sales_growth)
            ),
            "ebitda": average(
                as_whole_num(eval1.ebitda_pct_rev), as_whole_num(eval2.ebitda_pct_rev)
            ),
            "dpn": average(
                as_whole_num(eval1.dpn_pct_rev), as_whole_num(eval2.dpn_pct_rev)
            ),
            "tax rate": average(
                as_whole_num(eval1.tax_rate), as_whole_num(eval2.tax_rate)
            ),
            "nwc": average(
                as_whole_num(eval1.nwc_pct_rev), as_whole_num(eval2.nwc_pct_rev)
            ),
            "capex": average(
                as_whole_num(eval1.capex_pct_rev), as_whole_num(eval2.capex_pct_rev)
            ),
        }
        return avg

    @staticmethod
    def exit_app() -> None:
        """Terminate the application process."""
        logging.info("Application Ended")
        sys.exit()


# start app
Controller()

logging.info("Application Ended")
