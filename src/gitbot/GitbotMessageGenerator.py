import requests
import json
import logging

class GitbotMessageGenerator:

    AUTOFIX_OPT_KEY = "autofix"
    ISSUE_OPT_KEY = "issue"
    REPORT_OPT_KEY = "report"

    __BASE_URL = "https://services3.www.meterian.io/api/v1/gitbot/results/parse/"
    __log =  logging.getLogger("GitbotMessageGenerator")

    def __init__(self, requests_ssl_verify: bool = True):
        self.requests_ssl_verify = requests_ssl_verify

    def genMessage(self, report: map, options: map, exclusions: str = None) -> map:
        body = { "report": report, "options": options }
        headers = {"Content-Type": "application/json"}
        if exclusions is None:
            url = self.__BASE_URL
        else:
            url = self.__BASE_URL + "?exclude=" + exclusions

        response = requests.post(url, data = json.dumps(body), headers = headers, verify=self.requests_ssl_verify)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            self.__log.error("Unsuccessful call to gitbot\nStatus code: %s\nResponse: %s", str(response.status_code), response.text)
            return None