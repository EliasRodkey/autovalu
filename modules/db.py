#! python3
# controller.py -  handles interactions between user and backend by storing users input as python dictionaries in
# an SQL database

import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

import sqlite3, json


class DBHandler:
    def __init__(self):
        logging.debug("initiating DBHandler connection")
        self.conn = sqlite3.connect("local_db\\autovalu.db")
        self.c = self.conn.cursor()
        self.time = None

        # Initialize data base and current instance
        self.make_tables()

    # creates tables in database
    def make_tables(self):
        try:
            self.c.execute(
                "CREATE TABLE autovalu_data (date_time varchar(3), stock_id json, company_data json, inputs json)"
            )
        except Exception:
            pass
        try:
            self.c.execute("CREATE TABLE autovalu_searches (query text, results json)")
        except Exception:
            pass
        try:
            self.c.execute("CREATE TABLE autovalu_profiles (sec_id text, profile json)")
        except Exception:
            pass

    ###   DB Row Generators   ###
    def make_data_inst(self, stock, data, inputs):
        self.time = self.get_time()
        with self.conn:
            self.c.execute(
                "INSERT INTO autovalu_data VALUES (:date_time, :stock_id, :company_data, :inputs)",
                {
                    "date_time": self.time,
                    "stock_id": json.dumps(stock),
                    "company_data": json.dumps(data),
                    "inputs": json.dumps(inputs),
                },
            )
        logging.info("data for {} added to database".format(stock["ticker"]))

    def make_search_inst(self, query, search_results):
        with self.conn:
            self.c.execute(
                "INSERT INTO autovalu_searches VALUES (:query, :results)",
                {"query": query, "results": json.dumps(search_results)},
            )
        logging.info("search results for {} added to database".format(query))

    def make_profile_inst(self, sec_id, profile):
        with self.conn:
            self.c.execute(
                "INSERT INTO autovalu_profiles VALUES (:sec_id, :profile)",
                {"sec_id": sec_id, "profile": json.dumps(profile)},
            )
        logging.info("profile for {} added to database".format(sec_id))

    ###   DB Loaders   ###
    def all_past_inst(self):
        with self.conn:
            self.c.execute("SELECT date_time, stock_id FROM autovalu_data")
            history = self.c.fetchall()
        results = []
        for search in history:
            results.append((search[0], json.loads(search[1])))
        logging.info("past instances accessed")
        return results

    def load_searches(self, query):
        with self.conn:
            try:
                self.c.execute(
                    "SELECT results FROM autovalu_searches WHERE query = :query",
                    {"query": query},
                )
                result = json.loads(self.c.fetchone()[0])
                logging.info("search results for query {} found in db".format(query))
                return result
            except Exception:
                logging.info("no searches from query {} found in db".format(query))
                return None

    def load_profile(self, sec_id):
        with self.conn:
            try:
                self.c.execute(
                    "SELECT profile FROM autovalu_profiles WHERE sec_id = :sec_id",
                    {"sec_id": sec_id},
                )
                result = json.loads(self.c.fetchone()[0])
                logging.info("profile for security_id {} found in db".format(sec_id))
                return result
            except Exception:
                logging.info("no profiles from id {} found in db".format(sec_id))
                return None

    def load_data(self, time):
        with self.conn:
            self.c.execute(
                "SELECT * FROM autovalu_data WHERE date_time = :time", {"time": time}
            )
            results = self.c.fetchone()
            if results == None:
                logging.info("no data found for time stamp {}".format(time))
                return None
        result_dictionary = {}
        names = ("date_time", "stock_id", "company_data", "inputs")
        for result, name in zip(results, names):
            if result[0] == "{":
                result = json.loads(result)
                result_dictionary[name] = result
        logging.info("data found for time stamp {}".format(time))
        return result_dictionary

    @staticmethod
    def get_time():
        import datetime

        time = datetime.datetime.now()
        time_str = time.strftime("%D, %H:%M %S")
        return time_str


if __name__ == "__main__":

    DBHandler()
