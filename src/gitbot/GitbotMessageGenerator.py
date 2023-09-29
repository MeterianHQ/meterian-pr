import requests
import json
import logging
import os

class GitbotMessageGenerator:

    AUTOFIX_OPT_KEY = "autofix"
    ISSUE_OPT_KEY = "issue"
    REPORT_OPT_KEY = "report"

    __METERIAN_ENV = os.environ["METERIAN_ENV"] if "METERIAN_ENV" in os.environ and os.environ["METERIAN_ENV"] == "qa" else "www"
    __BASE_URL = "https://services3." + __METERIAN_ENV + ".meterian.io/api/v1/gitbot/results/parse/"
    __log =  logging.getLogger("GitbotMessageGenerator")

    def __init__(self):
        pass

    def genMessage(self, report: map, options: map, exclusions: str = None) -> map:
        body = { "report": report, "options": options }
        headers = {"Content-Type": "application/json"}
        if exclusions is None:
            response = requests.post(self.__BASE_URL, data = json.dumps(body), headers = headers)
        else:
            response = requests.post(self.__BASE_URL + "?exclude=" + exclusions , data = json.dumps(body), headers = headers)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            self.__log.error("Unsuccessful call to gitbot\nStatus code: %s\nResponse: %s", str(response.status_code), response.text)
            return None