import json
import logging

from rich.logging import RichHandler

from packages.linkedin import LinkedinScraper


class Crawler:
    def __init__(self, logger):
        self.worker = []
        # setup logger
        self.logger = logger

    def set_search_term(self):
        # read search term from file
        config = json.load(open("config.json"))
        search_term = config["search_term"]

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

        self.logger.info("Finished crawling, total {} new jobs".format(len(results)))


def setup_logger():
    # setup logger
    logger = logging.getLogger()
    logging.basicConfig(
        level="DEBUG",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    logger.setLevel(logging.DEBUG)
    return logger


if __name__ == "__main__":
    logger = setup_logger()
    app = Crawler(logger=logger)
    app.add_worker(LinkedinScraper(logger=logger))
    app.run()
