#! python3
# controller.py -  handles interactions between user and backend by storing users input as python dictionaries in
# an SQL database

import logging

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)

from view import Ui_View, QtGui, QtWidgets
from model import Model


class Controller:
    def __init__(self):
        # initialize view and model
        self.pages = {}
        self.page_history = []
        self.model = Model()
        self.api_obj = self.model.find()
        self.view = Ui_View(self)

        # define possible choices fro evaluations
        self.nwc_methods = (
            "As Reported",
            "(TCA-Cash)-(TCL-Debt)",
            "(A/R+Inventories-A/P)",
            "(TCA-TCL)",
        )
        self.eval_types = ("Historical", "Recent", "Custom")

        # define variable to determine if db or api is queried
        self.data_access_time = None
        self.load = False
        self.search_results = None

        # render search page to start app
        self.view.show_ui()

    ###   Page Changers   ###
    # decides what information to gather based on the page input
    def load_frame(self, page, inputs=None):
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
        # TODO add laod option
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

    ###   View Model Interacitons   ###
    # sends search query to api, stores results to database, or accesses database
    def send_search(self, query):
        if query == "":
            self.view.error("Please enter a search into the search bar")
            return
        logging.info("search query : {}".format(query))
        self.load = False
        in_db = self.model.db.load_searches(query)
        if in_db == None:
            self.search_results = self.api_obj.auto_complete_call(query)
            self.model.db.make_search_inst(query, self.search_results)
        else:
            self.api_obj.search_results = in_db
            self.search_results = in_db

        if len(self.search_results) == 0:
            self.view.error(
                "No search results found for {}\nPlease try another search".format(
                    query
                )
            )
            return
        self.pages[self.view.search_page.__name__].display_search_results(
            self.search_results
        )
        logging.debug("search_results : {}".format(self.search_results))

    def search_history(self, query):
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

    def update_company_profile(self):
        in_db = self.model.db.load_profile(self.chosen_company["securityId"])
        if in_db == None:
            self.company_profile = self.api_obj.company_profile_call(
                self.chosen_company["mic"], self.chosen_company["ticker"]
            )
            self.model.db.make_profile_inst(
                self.chosen_company["securityId"], self.company_profile
            )
        else:
            self.api_obj.company_profile = in_db
            self.company_profile = in_db
        self.pages[self.view.input_page.__name__].update_labels(self.company_profile)
        logging.debug("company profile collected : {}".format(self.company_profile))

    def update_inputs(self, inputs):
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

    def update_company_data(self):
        in_db = self.model.db.load_data(self.data_access_time)
        if in_db == None:
            self.api_obj.query_morningstar(self.chosen_company)
            self.company_data = self.model.gather(
                self.chosen_company, self.api_obj.data_object()
            )
            self.model.db.make_data_inst(
                self.chosen_company, self.api_obj.data_object(), self.inputs
            )
        else:
            data = in_db["company_data"]
            self.company_data = self.model.gather(self.chosen_company, data)

    def create_evaluations(self, inputs):
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
    # renders frame by rerunning the page code to reflect value updates
    def render_frame(self, page):
        # run or Rerun code for new page to ensure current data displayed
        self.pages[page.__name__] = page(self)
        new_page = self.pages[page.__name__]
        self.view.stackedWidget.addWidget(new_page)
        self.view.stackedWidget.setCurrentWidget(new_page)
        self.page_history.append(new_page)
        logging.debug("widget {} rendered".format(new_page.objectName()))

    def show_frame(self, page):
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

    def find_last_page(self):
        self.last_page = self.page_history[-2]
        if self.last_page == self.view.about_page:
            self.last_page = self.page_history[-1]
        return self.last_page

    ###   Unique Buttons   ###
    def back_button(self):
        last_page = self.page_history[-2]
        if last_page == self.pages[self.view.about_page.__name__]:
            last_page = self.page_history[-1]
        self.view.stackedWidget.setCurrentWidget(last_page)

    def save_button(self, parent):
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
    def input_error(self, page, inputs):
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
    def get_treeview_row(self, index):
        self.chosen_company["companyName"] = index.siblingAtColumn(0).data()
        self.chosen_company["ticker"] = index.siblingAtColumn(1).data()
        self.chosen_company["mic"] = index.siblingAtColumn(2).data()
        self.chosen_company["currency"] = index.siblingAtColumn(3).data()
        self.chosen_company["securityId"] = index.siblingAtColumn(4).data()
        self.chosen_company["endOfDayQuoteTicker"] = index.siblingAtColumn(5).data()
        self.data_access_time = index.siblingAtColumn(6).data()
        logging.info("results selected from treeview : {}".format(self.chosen_company))

    def find_expected_return(self):
        self.model.find.find_expected_return()

    def find_risk_free_rate(self):
        self.model.find.find_risk_free()

    ###   Other Methods   ###
    @staticmethod
    def eval_avg(eval1, eval2):
        def as_whole_num(num):
            return num * 100

        def average(val1, val2):
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
    def exit_app():
        import sys

        logging.info("Application Ended")
        sys.exit()


# start app
Controller()

logging.info("Application Ended")
