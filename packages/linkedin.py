import hashlib
import logging
import time
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


class LinkedinScraper:
    def __init__(self, kwmap: Dict[str, str]):
        self.base_url = "https://www.linkedin.com/jobs/search/?keywords="
        self.keywords = kwmap.values()
        self.search_term = []
        self.logger = logging.getLogger("LinkedIn")
        self.search_time = {
            "24h": "&f_TPR=r86400",
        }
        if len(self.keywords) > 0:
            # flatten list
            self.keywords = [item for sublist in self.keywords for item in sublist]

    def set_search_term(self, search_term: List[str]):
        self.search_term.extend(search_term)

    def parse_card(self, card) -> Dict[str, str]:
        # parse card
        job_title = card.find("h3", class_="base-search-card__title").text.strip()
        company_name = card.find("h4", class_="base-search-card__subtitle").text.strip()
        job_location = card.find(
            "span", class_="job-search-card__location"
        ).text.strip()
        job_link = card.find("a", class_="base-card__full-link").get("href", "")
        date_posted = card.find("time").get("datetime", "")
        job_id = hashlib.md5(job_link.encode()).hexdigest()

        # return if all fields are not empty
        if not all(
            [job_title, company_name, job_location, job_link, date_posted, job_id]
        ):
            self.logger.info("Missing fields, skipping")
            return None

        # parse tags
        keywords = []
        for term in self.keywords:
            if term.lower() in job_title.lower():
                keywords.append(term)

        return {
            "job_title": job_title,
            "company_name": company_name,
            "job_location": job_location,
            "job_link": job_link,
            "date_posted": date_posted,
            "job_id": job_id,
            "source": "LinkedIn",
            "keywords": keywords,
        }

    def search(self):
        self.logger.info("Starting LinkedIn search")
        res = []

        for term in self.search_term:
            self.logger.info("Searching for '{}'".format(term))
            url = "{}{}&location={}{}".format(
                self.base_url, term, "United States", self.search_time["24h"]
            )
            resp = requests.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            try:
                for card in soup.find(
                    "ul", class_="jobs-search__results-list"
                ).find_all("li"):
                    parsed_card = self.parse_card(card)
                    if parsed_card is not None:
                        res.append(parsed_card)
            except AttributeError:
                self.logger.info("No new jobs found for '{}'".format(term))
                continue

            self.logger.info(
                "Finished searching for '{}', total {} new jobs".format(term, len(res))
            )
            time.sleep(1)
        return res
