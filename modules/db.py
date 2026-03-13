#! python3
"""
db.py - SQLite database handler for AutoValu.

Caches search queries, company profiles, and completed evaluations locally to
reduce redundant API calls across sessions.

Classes:
    DBHandler: Manages the SQLite connection and all CRUD operations.

Tables:
    autovalu_data: Stores full evaluation records keyed by timestamp.
    autovalu_searches: Caches autocomplete results keyed by search query string.
    autovalu_profiles: Caches company profiles keyed by Morningstar security ID.
"""

import logging
import sqlite3
import json
import os
from typing import Optional

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DBHandler:
    """Manages the local SQLite database connection and all CRUD operations.

    Attributes:
        conn (sqlite3.Connection): The active database connection.
        c (sqlite3.Cursor): Cursor used for all query execution.
        time (str | None): Timestamp of the most recently written evaluation record.

    Methods:
        __init__: Open (or create) the SQLite database and initialize tables.
        make_tables: Create application tables if they do not already exist.
        make_data_inst: Insert a completed evaluation record into autovalu_data.
        make_search_inst: Cache autocomplete results for a query string.
        make_profile_inst: Cache a company profile by security ID.
        all_past_inst: Retrieve timestamps and stock IDs for all stored evaluations.
        load_searches: Retrieve cached autocomplete results by query string.
        load_profile: Retrieve a cached company profile by security ID.
        load_data: Retrieve a full evaluation record by timestamp.
        get_time: Return the current local datetime as a formatted string (static).
    """

    def __init__(self) -> None:
        """Open (or create) the local SQLite database and initialize all tables.

        Raises:
            sqlite3.OperationalError: If the database file path is not accessible.
        """
        logging.debug("initiating DBHandler connection")
        path = os.path.join(os.getcwd(), "local_db", "autovalu.db")
        self.conn = sqlite3.connect(path)
        self.c = self.conn.cursor()
        self.time: Optional[str] = None

        # Initialize data base and current instance
        self.make_tables()

    def make_tables(self) -> None:
        """Create the three application tables if they do not already exist."""
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
    def make_data_inst(self, stock: dict, data: dict, inputs: dict) -> None:
        """Insert a completed evaluation record into autovalu_data.

        Args:
            stock (dict): Company identifier fields (ticker, mic, securityId, etc.).
            data (dict): Raw API data object returned by APIData.data_object().
            inputs (dict): User-supplied DCF model parameters.
        """
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

    def make_search_inst(self, query: str, search_results: list) -> None:
        """Cache autocomplete search results for a given query string.

        Args:
            query (str): The search text submitted by the user.
            search_results (list): List of company result dicts returned by the API.
        """
        with self.conn:
            self.c.execute(
                "INSERT INTO autovalu_searches VALUES (:query, :results)",
                {"query": query, "results": json.dumps(search_results)},
            )
        logging.info("search results for {} added to database".format(query))

    def make_profile_inst(self, sec_id: str, profile: dict) -> None:
        """Cache a company profile keyed by its Morningstar security ID.

        Args:
            sec_id (str): Morningstar security identifier.
            profile (dict): Company profile dict returned by the API.
        """
        with self.conn:
            self.c.execute(
                "INSERT INTO autovalu_profiles VALUES (:sec_id, :profile)",
                {"sec_id": sec_id, "profile": json.dumps(profile)},
            )
        logging.info("profile for {} added to database".format(sec_id))

    ###   DB Loaders   ###
    def all_past_inst(self) -> list[tuple[str, dict]]:
        """Retrieve the timestamp and stock identifier for every stored evaluation.

        Returns:
            list[tuple[str, dict]]: List of (timestamp, stock_dict) pairs ordered
                                    by insertion sequence.
        """
        with self.conn:
            self.c.execute("SELECT date_time, stock_id FROM autovalu_data")
            history = self.c.fetchall()
        results = []
        for search in history:
            results.append((search[0], json.loads(search[1])))
        logging.info("past instances accessed")
        return results

    def load_searches(self, query: str) -> Optional[list]:
        """Retrieve cached autocomplete results for a query string.

        Args:
            query (str): The search text to look up.

        Returns:
            list | None: Cached results list, or None if the query is not in the database.
        """
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

    def load_profile(self, sec_id: str) -> Optional[dict]:
        """Retrieve a cached company profile by security ID.

        Args:
            sec_id (str): Morningstar security identifier.

        Returns:
            dict | None: Cached profile dict, or None if not found.
        """
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

    def load_data(self, time: Optional[str]) -> Optional[dict]:
        """Retrieve a full evaluation record by its timestamp.

        Args:
            time (str | None): Timestamp string as produced by get_time(), or None
                               when no prior evaluation has been selected.

        Returns:
            dict | None: Dictionary with 'date_time', 'stock_id', 'company_data', and
                         'inputs' keys if a matching record exists, otherwise None.
        """
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
    def get_time() -> str:
        """Return the current local date and time as a formatted string.

        Returns:
            str: Datetime string formatted as '%D, %H:%M %S' (e.g. '03/13/26, 14:05 22').
        """
        import datetime

        time = datetime.datetime.now()
        time_str = time.strftime("%D, %H:%M %S")
        return time_str


if __name__ == "__main__":

    DBHandler()
