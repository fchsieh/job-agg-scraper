import logging
import os

import toml
from rich.logging import RichHandler

from packages.db import DB
from packages.indeed import IndeedScraper
from packages.linkedin import LinkedinScraper


class Crawler:
    def __init__(self, logger):
        self.worker = []
        self.config = toml.load(os.path.join("..", "config.toml"))
        # setup logger
        self.logger = logger
        self.DB = DB(config=self.config)

    def set_search_term(self):
        # read search term from file
        job_title = self.config["search"]["job_title"]
        job_level = self.config["search"]["job_level"]
        # build search term
        search_term = [
            "{} {}".format(title, level) for level in job_level for title in job_title
        ]

        for worker in self.worker:
            worker.set_search_term(search_term)

    def add_worker(self, worker):
        self.worker.append(worker)

    def run(self):
        self.logger.info("Starting crawler")
        self.set_search_term()
        results = []
        for worker in self.worker:
            results.extend(worker.search())

        self.logger.info(
            "Finished crawling, total {} new jobs before filtering".format(len(results))
        )
        self.logger.info("Pushing data to database")

        date = [res["date_posted"] for res in results]
        formatted_data = {
            d: [res for res in results if res["date_posted"] == d] for d in set(date)
        }
        # remove duplicates by job_id
        for date, data in formatted_data.items():
            formatted_data[date] = list({v["job_id"]: v for v in data}.values())

        self.DB.push(formatted_data)


def setup_logger():
    # setup logger
    logger = logging.getLogger()
    logging.basicConfig(
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger.setLevel(logging.INFO)
    return logger


if __name__ == "__main__":
    logger = setup_logger()
    app = Crawler(logger=logger)
    app.add_worker(LinkedinScraper(kwmap=app.config["search"]))
    app.add_worker(IndeedScraper(kwmap=app.config["search"]))
    app.run()
