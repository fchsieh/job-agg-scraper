import logging
import re
import time
from typing import Dict, List

from bs4 import BeautifulSoup
import requests


class LinkedinScraper:
    def __init__(self, logger):
        self.base_url = "https://www.linkedin.com/jobs/search/?keywords="
        self.search_term = []
        self.logger = logging.getLogger("LinkedIn")
        self.search_time = {
            "24h": "&f_TPR=r86400",
        }

    def set_search_term(self, search_term: List[str]):
        self.search_term.extend(search_term)

    def parse_card(self, card) -> Dict[str, str]:
        # parse card
        job_title = card.find("h3", class_="base-search-card__title").text.strip()
        company_name = card.find("h4", class_="base-search-card__subtitle").text.strip()
        job_location = card.find(
            "span", class_="job-search-card__location"
        ).text.strip()
        job_link = card.find("a", class_="base-card__full-link")["href"]
        date_posted = card.find("time")["datetime"]
        job_id = re.search(r"(\d+)", job_link).group(1)

        return {
            "job_title": job_title,
            "company_name": company_name,
            "job_location": job_location,
            "job_link": job_link,
            "date_posted": date_posted,
            "job_id": job_id,
        }

    def search(self):
        res = []

        for term in self.search_term:
            self.logger.info("Searching for '{}'".format(term))
            url = "{}{}&location={}{}".format(
                self.base_url, term, "United States", self.search_time["24h"]
            )
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for card in soup.find("ul", class_="jobs-search__results-list").find_all(
                "li"
            ):
                res.append(self.parse_card(card))

            self.logger.info(
                "Finished searching for '{}', total {} new jobs".format(term, len(res))
            )
            time.sleep(1)
        return res
