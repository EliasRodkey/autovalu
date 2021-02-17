#! python3

# Form implementation generated from reading ui file 'view.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# view.py - pyqt5 gui rendering file for controller.py in AutoValu Applications
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import sys


class Ui_View(object):
    def __init__(self, controller):
        # access controller
        self.controller = controller

        # start application
        self.app = QtWidgets.QApplication(sys.argv)
        self.View = QtWidgets.QMainWindow()
        self.View.setWindowTitle("AutoValu")
        self.View.setWindowIcon(QtGui.QIcon("imgs\\logo.png"))

        # access style class
        self.STYLE = QtStyle()

        # access widget classes
        self.login_page = LoginPage
        self.search_page = SearchPage
        self.input_page = InputPage
        self.summary_page = SummaryPage
        self.about_page = AboutPage

        # access error popup
        self.error = ErrorPopup

        # add widgets
        self.setup_view(self.View)

    def show_ui(self):
        self.View.show()
        sys.exit(self.app.exec_())

    def setup_view(self, View):
        # set main window name and size
        View.setObjectName("View")
        View.resize(1500, 1200)
        View.setMinimumSize(QtCore.QSize(1500, 1200))
        View.setMaximumSize(QtCore.QSize(1500, 1200))

        # set autovalue icon
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap("imgs/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        View.setWindowIcon(icon)
        View.setWindowOpacity(1.0)

        # create main frame widget
        self.centralwidget = QtWidgets.QWidget(View)
        self.centralwidget.setObjectName("centralwidget")

        ## Menu Bar Widget ##
        self.menubar = QtWidgets.QMenuBar(View)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1500, 22))
        self.menubar.setStyleSheet(self.STYLE.menubar_style)
        self.menubar.setObjectName("menubar")

        # add help menu ot menubar
        self.menu_help = QtWidgets.QMenu(self.menubar)
        self.menu_help.setStyleSheet(
            'font: 8pt "MS Shell Dlg 2";\ncolor: rgb(255, 255, 255);'
        )
        self.menu_help.setObjectName("menu_help")
        self.menu_help.setTitle("Help")
        View.setMenuBar(self.menubar)

        # create find market return action
        self.action_find_market_return = QtWidgets.QAction(View)
        self.action_find_market_return.setObjectName("action_find_market_return")
        self.action_find_market_return.setText("Find Expected Market Return")
        self.action_find_market_return.setStatusTip("Open Market Risk Premia")
        self.action_find_market_return.setShortcut("Ctrl+M")
        self.action_find_market_return.triggered.connect(
            lambda: self.controller.find_expected_return()
        )

        # create find risk free rate of return action
        self.action_find_risk_free = QtWidgets.QAction(View)
        self.action_find_risk_free.setObjectName("action_find_risk_free")
        self.action_find_risk_free.setText("Find Risk Free Rate of Return")
        self.action_find_risk_free.setStatusTip("Open US Treasury Website")
        self.action_find_risk_free.setShortcut("Ctrl+F")
        self.action_find_risk_free.triggered.connect(
            lambda: self.controller.find_risk_free_rate()
        )

        # create navigate to about page action
        self.to_about_page = QtWidgets.QAction(View)
        self.to_about_page.setObjectName("to_about_page")
        self.to_about_page.setText("About")
        self.to_about_page.setStatusTip("About AutoValu")
        self.to_about_page.setShortcut("Ctrl+A")
        self.to_about_page.triggered.connect(
            lambda: self.controller.render_frame(AboutPage)
        )

        # create quit app action
        self.action_exit = QtWidgets.QAction(View)
        self.action_exit.setObjectName("action_exit")
        self.action_exit.setText("Exit")
        self.action_exit.setStatusTip("Quit AutoValu")
        self.action_exit.setShortcut("Esc")
        self.action_exit.triggered.connect(lambda: self.controller.exit_app())

        # add actions to the help menubar
        self.menu_help.addAction(self.action_find_market_return)
        self.menu_help.addAction(self.action_find_risk_free)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.to_about_page)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.action_exit)
        self.menubar.addAction(self.menu_help.menuAction())

        ## Stacked Widget ##
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        self.stackedWidget.setGeometry(QtCore.QRect(0, 0, 1500, 1200))
        self.stackedWidget.setMinimumSize(QtCore.QSize(1500, 1200))
        self.stackedWidget.setMaximumSize(QtCore.QSize(1500, 1200))
        self.stackedWidget.setStyleSheet("background-color: rgb(115, 115, 115)")
        self.stackedWidget.setObjectName("stackedWidget")

        # add login page to staked widgets
        first_page = self.login_page(self.controller)
        self.controller.page_history.append(first_page)
        self.controller.pages[self.login_page] = first_page
        self.stackedWidget.addWidget(self.controller.pages[self.login_page])

        # add central widget to the view window
        View.setCentralWidget(self.centralwidget)

        ## Status Bar Widget ##
        self.statusbar = QtWidgets.QStatusBar(View)
        self.statusbar.setStyleSheet(self.STYLE.statusbar_style)
        self.statusbar.setObjectName("statusbar")
        View.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(View)


class LoginPage(QtWidgets.QWidget):
    ## Login Page Widget ##
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.STYLE = QtStyle()
        self.make_widgets()

    def make_widgets(self):
        self.setObjectName("login_page")

        # add login background-image label
        self.STYLE.set_bg_img(self)

        # username input field
        self.username = QtWidgets.QLineEdit(self)
        self.username.setGeometry(QtCore.QRect(1000, 350, 250, 40))
        self.username.setFont(self.STYLE.input_font)
        self.username.setAutoFillBackground(False)
        self.username.setStyleSheet(self.STYLE.login_input_style)
        self.username.setObjectName("username")
        self.username.setStatusTip("Input Username")
        self.username.setPlaceholderText("Username")

        # password input field
        self.password = QtWidgets.QLineEdit(self)
        self.password.setGeometry(QtCore.QRect(1000, 400, 250, 40))
        self.password.setFont(self.STYLE.input_font)
        self.password.setAutoFillBackground(False)
        self.password.setStyleSheet(self.STYLE.login_input_style)
        self.password.setObjectName("password")
        self.password.setStatusTip("Input Password")
        self.password.setPlaceholderText("Password")

        # login button # TODO: make hover over change color
        self.login_button = QtWidgets.QPushButton(self)
        self.login_button.setGeometry(QtCore.QRect(1062.5, 450, 150, 40))
        self.login_button.setStyleSheet(self.STYLE.button_style)
        self.login_button.setObjectName("login_button")
        self.login_button.clicked.connect(
            lambda: self.controller.load_frame(SearchPage)
        )
        self.login_button.setStatusTip("Login")
        self.login_button.setText("Login")
        self.login_button.setShortcut("Return")


class SearchPage(QtWidgets.QWidget):
    ## Search Page Widget ##
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.STYLE = QtStyle()
        self.make_widgets()

    def make_widgets(self):
        self.setObjectName("search_page")

        # add search page background-image label
        self.STYLE.set_bg_img(self)

        # search bar
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setGeometry(QtCore.QRect(400, 405, 700, 55))
        self.search_bar.setFont(self.STYLE.search_font)
        self.search_bar.setStyleSheet(self.STYLE.search_bar_style)
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setStatusTip("Enter Search")
        self.search_bar.setPlaceholderText("Search")

        # make load button
        self.load_button = QtWidgets.QPushButton(self)
        self.load_button.setGeometry(QtCore.QRect(800, 475, 150, 40))
        self.load_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.load_button.setStyleSheet(self.STYLE.button_style)
        self.load_button.setCheckable(False)
        self.load_button.setObjectName("load_button")
        self.load_button.setStatusTip("Load History")
        self.load_button.setText("Load")
        self.load_button.setShortcut("L")
        self.load_button.clicked.connect(
            lambda: self.controller.search_history(self.search_bar.text())
        )

        # search button
        self.search_button = QtWidgets.QPushButton(self)
        self.search_button.setGeometry(QtCore.QRect(550, 475, 150, 40))
        self.search_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.search_button.setStyleSheet(self.STYLE.button_style)
        self.search_button.setCheckable(False)
        self.search_button.setObjectName("search_button")
        self.search_button.setStatusTip("Send Search")
        self.search_button.setText("Search")
        self.search_button.setShortcut("Return")
        self.search_button.clicked.connect(
            lambda: self.controller.send_search(self.search_bar.text())
        )

        # next page button
        self.search_page_next_button = QtWidgets.QPushButton(self)
        self.search_page_next_button.setGeometry(QtCore.QRect(675, 995, 150, 40))
        self.search_page_next_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.search_page_next_button.setStyleSheet(self.STYLE.button_style)
        self.search_page_next_button.setCheckable(False)
        self.search_page_next_button.setObjectName("search_page_next_button")
        self.search_page_next_button.setStatusTip("Next Page")
        self.search_page_next_button.setText("Next")
        self.search_page_next_button.setShortcut("Right")
        self.search_page_next_button.clicked.connect(
            lambda: self.controller.load_frame(InputPage)
        )

        # search results
        self.search_results_model = QtGui.QStandardItemModel(0, 7, self)
        self.search_results_model.setHeaderData(0, Qt.Horizontal, "Company Name")
        self.search_results_model.setHeaderData(1, Qt.Horizontal, "Ticker")
        self.search_results_model.setHeaderData(2, Qt.Horizontal, "MIC")
        self.search_results_model.setHeaderData(3, Qt.Horizontal, "Currency")
        self.search_results_model.setHeaderData(4, Qt.Horizontal, "Security ID")
        self.search_results_model.setHeaderData(5, Qt.Horizontal, "EOD Quote Ticker")
        self.search_results_model.setHeaderData(6, Qt.Horizontal, "Date and Time")
        self.search_results_table = QtWidgets.QTreeView(self)
        self.search_results_table.setModel(self.search_results_model)
        self.search_results_table.setGeometry(QtCore.QRect(300, 530, 900, 450))
        self.search_results_table.setColumnWidth(0, 300)
        self.search_results_table.setColumnWidth(1, 120)
        self.search_results_table.setColumnWidth(2, 120)
        self.search_results_table.setColumnWidth(3, 120)
        self.search_results_table.setColumnWidth(4, 200)
        self.search_results_table.setColumnWidth(5, 200)
        self.search_results_table.setColumnWidth(6, 250)
        self.search_results_table.setStyleSheet(self.STYLE.search_results_style)
        self.search_results_table.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.search_results_table.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.search_results_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.search_results_table.setSortingEnabled(True)
        self.search_results_table.setAlternatingRowColors(True)
        self.search_results_table.setObjectName("search_results_table")
        self.search_results_table.setStatusTip("Search Results")
        self.search_results_table.doubleClicked.connect(
            self.controller.get_treeview_row
        )

    def display_search_results(self, search_results, time_stamps=None):
        self.search_results_model.removeRows(0, self.search_results_model.rowCount())
        row = 0
        for result in search_results:
            self.search_results_model.insertRow(row)
            self.search_results_model.setData(
                self.search_results_model.index(row, 0), result["companyName"]
            )
            self.search_results_model.setData(
                self.search_results_model.index(row, 1), result["ticker"]
            )
            self.search_results_model.setData(
                self.search_results_model.index(row, 2), result["mic"]
            )
            self.search_results_model.setData(
                self.search_results_model.index(row, 3), result["currency"]
            )
            self.search_results_model.setData(
                self.search_results_model.index(row, 4), result["securityId"]
            )
            self.search_results_model.setData(
                self.search_results_model.index(row, 5), result["endOfDayQuoteTicker"]
            )
            if self.controller.load:
                self.search_results_model.setData(
                    self.search_results_model.index(row, 6), time_stamps[row]
                )
            else:
                self.search_results_model.setData(
                    self.search_results_model.index(row, 6),
                    self.controller.model.db.get_time(),
                )
            row += 1


class InputPage(QtWidgets.QWidget):
    ## Input Page Widget ##
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.STYLE = QtStyle()
        self.make_widgets()

    def make_widgets(self):
        self.setObjectName("input_page")

        # add input background-image label
        self.STYLE.set_bg_img(self)

        # last page button
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.setGeometry(QtCore.QRect(300, 995, 150, 40))
        self.back_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.back_button.setStyleSheet(self.STYLE.button_style)
        self.back_button.setObjectName("back_button")
        self.back_button.setStatusTip("Last Page")
        self.back_button.setText("Back")
        self.back_button.setShortcut("Left")
        self.back_button.clicked.connect(lambda: self.controller.show_frame(SearchPage))

        # next button
        self.next_button = QtWidgets.QPushButton(self)
        self.next_button.setGeometry(QtCore.QRect(1050, 995, 150, 40))
        self.next_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.next_button.setStyleSheet(self.STYLE.button_style)
        self.next_button.setObjectName("next_button")
        self.next_button.setStatusTip("Next Page")
        self.next_button.setText("Next")
        self.next_button.setShortcut("Return")
        self.next_button.clicked.connect(
            lambda: self.controller.load_frame(SummaryPage, inputs=self.get_inputs())
        )

        # comapny profile information labels
        self.company_name_label = QtWidgets.QLabel(self)
        self.company_name_label.setGeometry(QtCore.QRect(200, 180, 650, 100))
        self.company_name_label.setFont(self.STYLE.title_font)
        self.company_name_label.setStyleSheet(self.STYLE.profile_label_style)
        self.company_name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.company_name_label.setObjectName("company_name_label")
        self.company_name_label.setStatusTip("Company Name")
        self.company_name_label.setText("COMPANY NAME")

        self.company_mic_label = QtWidgets.QLabel(self)
        self.company_mic_label.setGeometry(QtCore.QRect(200, 280, 650, 50))
        self.company_mic_label.setFont(self.STYLE.input_font)
        self.company_mic_label.setStyleSheet(self.STYLE.profile_label_style)
        self.company_mic_label.setObjectName("company_mic_label")
        self.company_mic_label.setStatusTip("Company MIC")
        self.company_mic_label.setText("MIC")

        self.company_ticker_label = QtWidgets.QLabel(self)
        self.company_ticker_label.setGeometry(QtCore.QRect(200, 330, 650, 50))
        self.company_ticker_label.setFont(self.STYLE.input_font)
        self.company_ticker_label.setStyleSheet(self.STYLE.profile_label_style)
        self.company_ticker_label.setObjectName("company_ticker_label")
        self.company_ticker_label.setStatusTip("Company Ticker")
        self.company_ticker_label.setText("TICKER")

        self.company_Industry_label = QtWidgets.QLabel(self)
        self.company_Industry_label.setGeometry(QtCore.QRect(200, 380, 650, 50))
        self.company_Industry_label.setFont(self.STYLE.input_font)
        self.company_Industry_label.setStyleSheet(self.STYLE.profile_label_style)
        self.company_Industry_label.setObjectName("company_Industry_label")
        self.company_Industry_label.setStatusTip("Company Industry")
        self.company_Industry_label.setText("INDUSTRY")

        self.company_sector_label = QtWidgets.QLabel(self)
        self.company_sector_label.setGeometry(QtCore.QRect(200, 430, 650, 50))
        self.company_sector_label.setFont(self.STYLE.input_font)
        self.company_sector_label.setStyleSheet(self.STYLE.profile_label_style)
        self.company_sector_label.setObjectName("company_sector_label")
        self.company_sector_label.setStatusTip("Company Sector")
        self.company_sector_label.setText("SECTOR")

        self.company_description_label = QtWidgets.QLabel(self)
        self.company_description_label.setGeometry(QtCore.QRect(200, 480, 650, 400))
        self.company_description_label.setFont(self.STYLE.body_font)
        self.company_description_label.setStyleSheet(self.STYLE.profile_body_style)
        self.company_description_label.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
        )
        self.company_description_label.setWordWrap(True)
        self.company_description_label.setObjectName("company_description_label")
        self.company_description_label.setStatusTip("Company Description")
        self.company_description_label.setText("COMPANY DESCRIPTION")

        ## input frames
        # nwc method frame
        self.frame = QtWidgets.QFrame(self)
        self.frame.setGeometry(QtCore.QRect(900, 180, 400, 100))
        self.frame.setStyleSheet(self.STYLE.input_frame_style)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        # nwc frame label
        self.nwc_label = QtWidgets.QLabel(self.frame)
        self.nwc_label.setGeometry(QtCore.QRect(0, 0, 400, 40))
        self.nwc_label.setFont(self.STYLE.body_font)
        self.nwc_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.nwc_label.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
        )
        self.nwc_label.setWordWrap(True)
        self.nwc_label.setObjectName("nwc_label")
        self.nwc_label.setStatusTip("NWC Calculation Method")
        self.nwc_label.setText("NWC Calculation Method")
        # nwc input
        self.nwc_combobox = QtWidgets.QComboBox(self.frame)
        self.nwc_combobox.setGeometry(QtCore.QRect(0, 30, 400, 60))
        self.nwc_combobox.setFont(self.STYLE.input_font)
        self.nwc_combobox.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.nwc_combobox.setObjectName("nwc_combobox")
        self.nwc_combobox.addItem("")
        self.nwc_combobox.addItem("")
        self.nwc_combobox.addItem("")
        self.nwc_combobox.addItem("")
        self.nwc_combobox.setStatusTip("NWC Calculation Method Selection")
        self.nwc_combobox.setItemText(0, "As Reported")
        self.nwc_combobox.setItemText(1, "(TCA-Cash)-(TCL-Debt)")
        self.nwc_combobox.setItemText(2, "A/R+Inventories-A/P")
        self.nwc_combobox.setItemText(3, "TCA-TCL")

        # proj_years frame
        self.frame_2 = QtWidgets.QFrame(self)
        self.frame_2.setGeometry(QtCore.QRect(900, 330, 400, 100))
        self.frame_2.setStyleSheet(self.STYLE.input_frame_style)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        # proj_years label
        self.proj_years_label = QtWidgets.QLabel(self.frame_2)
        self.proj_years_label.setGeometry(QtCore.QRect(0, 0, 400, 40))
        self.proj_years_label.setFont(self.STYLE.body_font)
        self.proj_years_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.proj_years_label.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
        )
        self.proj_years_label.setWordWrap(True)
        self.proj_years_label.setObjectName("proj_years_label")
        self.proj_years_label.setStatusTip("Years to Project Cash Flows")
        self.proj_years_label.setText("Years to Project Cash Flows")
        # proj_years input
        self.proj_years_spinbox = QtWidgets.QSpinBox(self.frame_2)
        self.proj_years_spinbox.setGeometry(QtCore.QRect(0, 30, 400, 60))
        self.proj_years_spinbox.setFont(self.STYLE.input_font)
        self.proj_years_spinbox.setStyleSheet(self.STYLE.input_frame_style)
        self.proj_years_spinbox.setAlignment(QtCore.Qt.AlignCenter)
        self.proj_years_spinbox.setSingleStep(5)
        self.proj_years_spinbox.setProperty("value", 5)
        self.proj_years_spinbox.setObjectName("proj_years_spinbox")
        self.proj_years_spinbox.setStatusTip("Years to Project Cash Flows Selection")

        # terminal growth input frame
        self.frame_4 = QtWidgets.QFrame(self)
        self.frame_4.setGeometry(QtCore.QRect(900, 480, 400, 100))
        self.frame_4.setStyleSheet(self.STYLE.input_frame_style)
        self.frame_4.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_4.setObjectName("frame_4")
        # terminal growth rate input label
        self.terminal_growth_label = QtWidgets.QLabel(self.frame_4)
        self.terminal_growth_label.setGeometry(QtCore.QRect(0, 0, 400, 40))
        self.terminal_growth_label.setFont(self.STYLE.body_font)
        self.terminal_growth_label.setStyleSheet(
            "background-color: rgb(255, 255, 255);"
        )
        self.terminal_growth_label.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
        )
        self.terminal_growth_label.setWordWrap(True)
        self.terminal_growth_label.setObjectName("terminal_growth_label")
        self.terminal_growth_label.setStatusTip("Terminal Growth")
        self.terminal_growth_label.setText("Terminal Growth Rate")
        # terminal growth rate input field
        self.terminal_growth_input = QtWidgets.QLineEdit(self.frame_4)
        self.terminal_growth_input.setGeometry(QtCore.QRect(0, 30, 400, 60))
        self.terminal_growth_input.setFont(self.STYLE.input_font)
        self.terminal_growth_input.setStyleSheet(self.STYLE.input_frame_style)
        self.terminal_growth_input.setAlignment(QtCore.Qt.AlignCenter)
        self.terminal_growth_input.setPlaceholderText("")
        self.terminal_growth_input.setObjectName("terminal_growth_input")
        self.terminal_growth_input.setStatusTip("Terminal Growth Input")
        self.terminal_growth_input.setText("2")

        # risk_free_rate input frame
        self.frame_3 = QtWidgets.QFrame(self)
        self.frame_3.setGeometry(QtCore.QRect(900, 630, 400, 100))
        self.frame_3.setStyleSheet(self.STYLE.input_frame_style)
        self.frame_3.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_3.setObjectName("frame_3")
        # risk free rate input label
        self.risk_free_rate_label = QtWidgets.QLabel(self.frame_3)
        self.risk_free_rate_label.setGeometry(QtCore.QRect(0, 0, 400, 40))
        self.risk_free_rate_label.setFont(self.STYLE.body_font)
        self.risk_free_rate_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.risk_free_rate_label.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
        )
        self.risk_free_rate_label.setWordWrap(True)
        self.risk_free_rate_label.setObjectName("risk_free_rate_label")
        self.risk_free_rate_label.setStatusTip("Risk Free Rate of Return")
        self.risk_free_rate_label.setText("Risk Free Rate of Return")
        # risk free rate input field
        self.risk_free_rate_input = QtWidgets.QLineEdit(self.frame_3)
        self.risk_free_rate_input.setGeometry(QtCore.QRect(0, 30, 400, 60))
        self.risk_free_rate_input.setFont(self.STYLE.input_font)
        self.risk_free_rate_input.setStyleSheet(self.STYLE.input_frame_style)
        self.risk_free_rate_input.setAlignment(QtCore.Qt.AlignCenter)
        self.risk_free_rate_input.setObjectName("risk_free_rate_input")
        self.risk_free_rate_input.setStatusTip("Risk Free Rateof Return Input")
        self.risk_free_rate_input.setPlaceholderText("See Help Menu for Current Rate")

        # market return input frame
        self.frame_5 = QtWidgets.QFrame(self)
        self.frame_5.setGeometry(QtCore.QRect(900, 780, 400, 100))
        self.frame_5.setStyleSheet(self.STYLE.input_frame_style)
        self.frame_5.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_5.setObjectName("frame_5")
        # market return input label
        self.market_return_label = QtWidgets.QLabel(self.frame_5)
        self.market_return_label.setGeometry(QtCore.QRect(0, 0, 400, 40))
        self.market_return_label.setFont(self.STYLE.body_font)
        self.market_return_label.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.market_return_label.setAlignment(
            QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft
        )
        self.market_return_label.setWordWrap(True)
        self.market_return_label.setObjectName("market_return_label")
        self.market_return_label.setStatusTip("Expected Market Rate of Return")
        self.market_return_label.setText("Expected Market Rate of Return")
        # market return input field
        self.market_return_input = QtWidgets.QLineEdit(self.frame_5)
        self.market_return_input.setGeometry(QtCore.QRect(0, 30, 400, 60))
        self.market_return_input.setFont(self.STYLE.input_font)
        self.market_return_input.setStyleSheet(self.STYLE.input_frame_style)
        self.market_return_input.setAlignment(QtCore.Qt.AlignCenter)
        self.market_return_input.setObjectName("market_return_input")
        self.market_return_input.setStatusTip("Expected Market Rate of Return Input")
        self.market_return_input.setPlaceholderText("See Help Menu for Current Rate")

    def update_labels(self, profile):
        self.company_name_label.setText(self.controller.chosen_company["companyName"])
        self.company_ticker_label.setText(self.controller.chosen_company["ticker"])
        self.company_mic_label.setText(self.controller.chosen_company["mic"])
        self.company_sector_label.setText(profile["sector"]["value"])
        self.company_Industry_label.setText(profile["industry"]["value"])
        self.company_description_label.setText(profile["businessDescription"]["value"])

    def get_inputs(self):
        inputs = {
            "nwc_method": (self.nwc_combobox.currentText(), str),
            "proj_years": (self.proj_years_spinbox.text(), int),
            "terminal_growth": (self.terminal_growth_input.text(), float),
            "risk_free_rate": (self.risk_free_rate_input.text(), float),
            "market_return": (self.market_return_input.text(), float),
        }
        return inputs


class SummaryPage(QtWidgets.QWidget):
    ## Summary Page Widget ##
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.STYLE = QtStyle()
        self.make_widgets()

    def make_widgets(self):
        self.setObjectName("summary_page")

        # add Summary background-image label
        self.STYLE.set_bg_img(self)

        # create back button
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.setGeometry(QtCore.QRect(300, 995, 150, 40))
        self.back_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.back_button.setStyleSheet(self.STYLE.button_style)
        self.back_button.setCheckable(False)
        self.back_button.setObjectName("back_button")
        self.back_button.setStatusTip("Last Page")
        self.back_button.setText("Back")
        self.back_button.setShortcut("Left")
        self.back_button.clicked.connect(lambda: self.controller.show_frame(InputPage))

        # create new valuation button
        self.new_button = QtWidgets.QPushButton(self)
        self.new_button.setGeometry(QtCore.QRect(1050, 995, 150, 40))
        self.new_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.new_button.setStyleSheet(self.STYLE.button_style)
        self.new_button.setCheckable(False)
        self.new_button.setObjectName("new_button")
        self.new_button.setStatusTip("Next Page")
        self.new_button.setText("New")
        self.new_button.setShortcut("Right")
        self.new_button.clicked.connect(lambda: self.controller.show_frame(SearchPage))

        # create save button
        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setGeometry(QtCore.QRect(675, 995, 150, 40))
        self.save_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.save_button.setStyleSheet(self.STYLE.button_style)
        self.save_button.setCheckable(False)
        self.save_button.setObjectName("save_button")
        self.save_button.setStatusTip("Export to Excel")
        self.save_button.setText("Save")
        self.save_button.setShortcut("Return")
        self.save_button.clicked.connect(
            lambda: self.controller.save_button(self.controller.view.View)
        )
        # create final eval frame
        self.eval_frame = QtWidgets.QFrame(self)
        self.eval_frame.setGeometry(QtCore.QRect(300, 405, 900, 550))
        self.eval_frame.setStyleSheet(self.STYLE.eval_frame_style)
        self.eval_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.eval_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.eval_frame.setObjectName("eval_frame")
        self.eval_frame.setStatusTip("Evaluation Summary")
        # company name
        self.company_name_label = QtWidgets.QLabel(self.eval_frame)
        self.company_name_label.setGeometry(QtCore.QRect(0, 20, 900, 50))
        self.company_name_label.setFont(self.STYLE.title_font)
        self.company_name_label.setStyleSheet("border-style: flat;")
        self.company_name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.company_name_label.setObjectName("company_name_label")
        self.company_name_label.setStatusTip("Company Name")
        self.company_name_label.setText("COMPANY NAME")
        # final verdict
        self.final_verdict_label = QtWidgets.QLabel(self.eval_frame)
        self.final_verdict_label.setGeometry(QtCore.QRect(0, 70, 900, 200))
        self.final_verdict_label.setFont(self.STYLE.search_font)
        self.final_verdict_label.setStyleSheet("border-style: flat;")
        self.final_verdict_label.setAlignment(QtCore.Qt.AlignCenter)
        self.final_verdict_label.setObjectName("final_verdict_label")
        self.final_verdict_label.setStatusTip("Final Verdict")
        self.final_verdict_label.setText("FINAL VERDICT")
        # disclaimer label
        self.disclaim_label = QtWidgets.QLabel(self.eval_frame)
        self.disclaim_label.setGeometry(QtCore.QRect(200, 300, 500, 200))
        self.disclaim_label.setFont(self.STYLE.body_font)
        self.disclaim_label.setStyleSheet("border-style: flat;")
        self.disclaim_label.setAlignment(QtCore.Qt.AlignCenter)
        self.disclaim_label.setWordWrap(True)
        self.disclaim_label.setObjectName("disclaim_label")
        self.disclaim_label.setStatusTip("Next Steps")
        self.disclaim_label.setText(
            "For further security analysis save this evaluation using the button below, from there you can edit your inputs and have access to more precise model assumptions, until reasonable assumptions are input into the excel model, this evaluation can not be considered complete"
        )

    def update_labels(self, assessment):
        self.company_name_label.setText(
            "{} Appears to be:".format(self.controller.chosen_company["companyName"])
        )
        try:
            self.final_verdict_label.setText(
                "{} by {}:\nThats {}!".format(
                    assessment[0], assessment[2], assessment[1]
                )
            )
        except IndexError:
            logging.error(
                "Assessment method return value too short length : {}, value : {} ".format(
                    len(assessment), assessment
                )
            )
            self.final_verdict_label.setText(
                "hmm, that's strange, something went wrong\nPlease try again!"
            )


class AboutPage(QtWidgets.QWidget):
    ## About Page Widget ##
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.STYLE = QtStyle()
        self.make_widgets()

    def make_widgets(self):
        self.setObjectName("about_page")

        # add About background-image label
        self.STYLE.set_bg_img(self)

        # create back button
        self.back_button = QtWidgets.QPushButton(self)
        self.back_button.setGeometry(QtCore.QRect(675, 995, 150, 40))
        self.back_button.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.back_button.setStyleSheet(self.STYLE.button_style)
        self.back_button.setCheckable(False)
        self.back_button.setObjectName("back_button")
        self.back_button.setStatusTip("Last Page")
        self.back_button.setText("Back")
        self.back_button.setShortcut("Left")
        self.back_button.clicked.connect(lambda: self.controller.back_button())

        # create about autovalu frame
        self.about_frame = QtWidgets.QFrame(self)
        self.about_frame.setGeometry(QtCore.QRect(300, 405, 900, 550))
        self.about_frame.setStyleSheet(self.STYLE.eval_frame_style)
        self.about_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.about_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.about_frame.setObjectName("about_frame")
        self.about_frame.setStatusTip("Evaluation Summary")

        # create about autovalu label
        self.about_label = QtWidgets.QLabel(self.about_frame)
        self.about_label.setGeometry(QtCore.QRect(0, 20, 900, 50))
        self.about_label.setFont(self.STYLE.title_font)
        self.about_label.setStyleSheet("border-style: flat;")
        self.about_label.setAlignment(QtCore.Qt.AlignCenter)
        self.about_label.setObjectName("about_label")
        self.about_label.setStatusTip("About")
        self.about_label.setText("About AutoValu")

        # set about body text
        self.about_body_label = QtWidgets.QLabel(self.about_frame)
        self.about_body_label.setGeometry(QtCore.QRect(50, 100, 800, 400))
        self.about_body_label.setFont(self.STYLE.body_font)
        self.about_body_label.setStyleSheet(
            "border-style: 0px;\nborder-color: rgb(255, 255, 255);"
        )
        self.about_body_label.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
        )
        self.about_body_label.setWordWrap(True)
        self.about_body_label.setObjectName("label")
        self.about_body_label.setStatusTip("About AutoValu")
        self.about_body_label.setText(
            """        AutoValu is a tool for for evaluating stocks by predicting the present value of a companies predicted future cash inflows to see how much a company is worth per share based on current and past cash flows.
        This method of evaluation if refered to as a Discounted Cash Flow analysis (DCF) and is intended to be used alongside other valuation methods such as multiples analysis, ratio analysis, or net asset evaluation.
        This application uses the Morningstar API to gather financial, statistical, and stock data. for detailed information about the calculations of the model, see the excel sheet produced at the end of each evaluation or look up DCF evaluation on google."""
        )


class ErrorPopup(QtWidgets.QMessageBox):
    def __init__(self, msg):
        super().__init__()
        self.setIcon(QtWidgets.QMessageBox.Critical)
        # self.setWindowIcon(QtGui.QIcon('imgs/error.jpg'))
        self.setText("oopsy!")
        self.setInformativeText(msg)
        self.setWindowTitle("AutoValu Error")
        self.exec_()


class QtStyle:
    def __init__(self):
        # widget style sheets
        self.button_style = """background-color: rgb(83, 162, 77);
                                                border-style: outset;
                                                border-color: rgb(255, 255, 255);
                                                border-width: 1px;
                                                border-radius: 5px;
                                                color: rgb(255, 255, 255);
                                                QPushButton :: hover
                                                {
                                                        background-color : white;
                                                }"""
        self.login_input_style = """background-color: rgb(255, 255, 255);
                                                border-color: rgb(231, 231, 231);
                                                border-radius: 5px;"""
        self.search_bar_style = """background-color: rgb(255, 255, 255);
                                                border-color: rgb(231, 231, 231);
                                                border-radius: 10px;"""
        self.search_results_style = """background-color: rgb(255, 255, 255);
                                                border-color: rgb(144, 144, 144);
                                                border-width: 2px;
                                                border-style: outset;
                                                border-radius: 10px;"""
        self.profile_label_style = """background-color: rgb(83, 162, 77);
                                                border-color: rgb(255, 255, 255);
                                                border-width: 1px;
                                                border-radius: 1px;
                                                border-style: outset;
                                                color: rgb(255, 255, 255);"""
        self.profile_body_style = """background-color: rgb(255, 255, 255);
                                                border-color: rgb(0, 0, 0);
                                                border-top-color: rgb(255, 255, 255);
                                                border-width: 1px;
                                                border-radius: 1px;
                                                border-style: outset;"""
        self.input_frame_style = """border-radius: 5px;
                                                border-color: rgb(186, 186, 186);
                                                border-width: 0.5px;
                                                border-style: outset;
                                                background-color: rgb(255, 255, 255);"""
        self.eval_frame_style = """background-color: rgb(255, 255, 255);
                                                border-style: outset;
                                                border-radius: 15px;
                                                border-width: 1px;
                                                border-color:rgb(97, 97, 97);"""
        self.menubar_style = """background-color: rgb(95, 95, 95);
                                                color: rgb(255, 255, 255);"""
        self.statusbar_style = """font: 8pt \"MS Shell Dlg 2\";
                                                color: rgb(255, 255, 255);
                                                border-color: rgb(144, 144, 144);
                                                background-color: rgb(0, 0, 0);"""

        # font desciptors
        self.input_font = QtGui.QFont()
        self.input_font.setFamily("Segoe UI")
        self.input_font.setPointSize(10)
        self.search_font = QtGui.QFont()
        self.search_font.setFamily("Segoe UI")
        self.search_font.setPointSize(12)
        self.body_font = QtGui.QFont()
        self.body_font.setFamily("Segoe UI")
        self.body_font.setPointSize(8)
        self.title_font = QtGui.QFont()
        self.title_font.setFamily("Segoe UI")
        self.title_font.setPointSize(14)

    def set_bg_img(self, page):
        bg_img = QtWidgets.QLabel(page)
        bg_img.setGeometry(QtCore.QRect(-10, 0, 1700, 1200))
        bg_img.setPixmap(QtGui.QPixmap("imgs\\bg_img.png"))
        bg_img.setScaledContents(True)
