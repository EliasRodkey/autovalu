#! python3
# model.py - contains instance of modules used in calculations in autovalu

import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

from modules import db, api, evaluation, excel


class Model:
    def __init__(self):
        self.db = db.DBHandler()
        self.find = api.APIData
        self.gather = api.DataValues
        self.evaluate = evaluation.Evaluation
        self.make_wb = excel.MakeWB
