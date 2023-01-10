import hashlib
import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Dict, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class IndeedScraper:
    def __init__(self, kwmap: Dict[str, str]):
        self.base_url = "https://www.indeed.com/jobs?"
        self.keywords = kwmap.values()
        self.search_term = []
        self.logger = logging.getLogger("Indeed")
        self.search_time = {
            "24h": "1",
            "7d": "7",
        }
        if len(self.keywords) > 0:
            # flatten list
            self.keywords = [item for sublist in self.keywords for item in sublist]

        self.driver = self._set_driver()

    def _set_driver(self):
        logging.getLogger("WDM").setLevel(logging.WARNING)  # suppress wdm logs
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
        )
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--incognito")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

    def set_search_term(self, search_term: List[str]):
        self.search_term.extend(search_term)

    def parse_card(self, card) -> Dict[str, str]:
        job_title = card.find("h2").getText()
        parsed_job_url = card.select_one("h2 a")["href"].replace("/rc/clk?", "viewjob?")
        job_link = "https://www.indeed.com/" + parsed_job_url
        company_name = card.find(attrs={"class": "companyName"}).getText()
        job_location = card.find(attrs={"class": "companyLocation"}).getText()
        # remove postal code
        job_location = re.sub(r"\d{5}", "", job_location).strip()
        job_id = hashlib.md5(job_link.encode()).hexdigest()
        # parse date posted
        date_posted = card.find(attrs={"class": "date"}).getText()
        if "Today" in date_posted or "Just" in date_posted:
            date_posted = date.today().strftime("%Y-%m-%d")
        elif "Yesterday" in date_posted:
            date_posted = datetime.strftime(date.today() - timedelta(1), "%Y-%m-%d")
        elif "ago" in date_posted:
            # get * days in string
            date_posted = re.search(r"(\d+) day", date_posted).group(1)
            # convert to int
            date_posted = int(date_posted)
            # subtract days from today
            date_posted = datetime.strftime(
                date.today() - timedelta(date_posted), "%Y-%m-%d"
            )
        else:
            # otherwise, use today's date
            date_posted = date.today().strftime("%Y-%m-%d")

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
            "source": "Indeed",
            "keywords": keywords,
        }

    def search(self):
        self.logger.info("Starting Indeed search")
        res = []

        for term in self.search_term:
            self.logger.info("Searching for '{}'".format(term))
            url = "{}q={}&l={}&fromage={}".format(
                self.base_url, term, "United States", self.search_time["24h"]
            )
            self.driver.get(url)
            self.driver.implicitly_wait(10)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            try:
                cards = soup.find_all(attrs={"class": "job_seen_beacon"})
                for card in cards:
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

        self.driver.quit()
        return res
