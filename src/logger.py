import json
import logging
from os import environ

import requests


class CustomLoggerHandler(logging.Handler):
    def __init__(self, api_url, api_headers, api_auth=None):
        super().__init__()
        self.api_url = api_url
        self.api_headers = api_headers
        self.api_auth = api_auth

    def emit(self, record):
        log_entry = self.format(record)  # Format the log message

        # Log to console
        print(log_entry)

        # Log to OpenObservce
        try:
            log_data = [
                {"level": record.levelname, "job": "tradingbot", "log": log_entry}
            ]
            data = json.dumps(log_data)

            response = requests.post(
                self.api_url,
                headers=self.api_headers,
                data=data,
                verify=True,
                auth=self.api_auth,
            )
            if response.status_code != 200:
                print(
                    f"Failed to log to OpenObservce. Status code: {response.status_code}"
                )
        except Exception as e:
            print(f"Failed to log to OpenObservce: {str(e)}")


# Configure the logging module
logging.basicConfig(level=logging.INFO)

# Create an instance of the custom logger handler
api_headers = {"Content-Type": "application/json"}
custom_handler = CustomLoggerHandler(
    environ.get("OPENOBSERVE_URL"),
    api_headers,
    (environ.get("OPENOBSERVE_USER"), environ.get("OPENOBSERVE_PASSWORD")),
)

# Create a logger and add the custom handler
logger = logging.getLogger("custom_logger")
logger.addHandler(custom_handler)
