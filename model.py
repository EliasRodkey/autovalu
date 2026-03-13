#! python3
"""
model.py - Facade module aggregating all backend modules for the AutoValu application.

Classes:
    Model: Central facade that initializes and exposes all backend module classes
           as attributes for use by the controller.
"""

import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

from modules import db, api, evaluation, excel


class Model:
    """Thin facade that initializes all backend modules and exposes them as attributes.

    Attributes:
        db       (db.DBHandler):          Active SQLite database connection and handler.
        find     (type[api.APIData]):      APIData class reference for making API calls.
        gather   (type[api.DataValues]):   DataValues class reference for parsing API responses.
        evaluate (type[evaluation.Evaluation]): Evaluation class reference for DCF calculations.
        make_wb  (type[excel.MakeWB]):    MakeWB class reference for exporting Excel workbooks.

    Methods:
        __init__: Initialize all backend module instances and class references.
    """

    def __init__(self) -> None:
        """Initialize all backend module instances and class references."""
        self.db = db.DBHandler()
        self.find = api.APIData
        self.gather = api.DataValues
        self.evaluate = evaluation.Evaluation
        self.make_wb = excel.MakeWB
