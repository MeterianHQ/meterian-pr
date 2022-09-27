import json
import logging

class End2EndTestFunctions:

    log = logging.getLogger("End2EndTestFunctions")

    def read_JSON_report(report_path):
        meterian_report = open(report_path)
        meterian_json_report = json.load(meterian_report)
        meterian_report.close()
        return meterian_json_report

    def init_logging(level: int):

        logging.basicConfig(
            level = level,
            format='%(asctime)-15s - %(levelname)-6s - %(name)s :: %(message)s'
        )

        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            logger.setLevel(level)
        
        End2EndTestFunctions.log.debug('Logging initiated')