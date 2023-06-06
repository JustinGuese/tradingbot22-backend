# https://medium.com/@sharan.aadarsh/sending-notification-to-slack-using-python-8b71d4f622f3

import json
import sys
from os import environ

import requests

SEVERITIES = {
    "error" : {
        "emoji" : ":collision:",
        "title" : "Error Tradingbot22! ",
        "color" : "#FF0000"
    },
    "info" : {
        "emoji" : ":information_source:",
        "title" : "Tradingbot22 Info: ",
        "color" : "#0000FF"
    }
}

SLACKURL = environ.get("SLACKURL","https://hooks.slack.com/services/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")

def sendToSlack(botname, message: str, severity = "info"):
    message = (message)
    title = (SEVERITIES[severity]["title"])
    slack_data = {
        "username": botname,
        "icon_emoji": SEVERITIES[severity]["emoji"],
        "channel": "#tradingbot22-messages",
        "attachments": [
            {
                "color": SEVERITIES[severity]["color"],
                "fields": [
                    {
                        "title": title,
                        "value": message,
                        "short": "false",
                    }
                ]
            }
        ]
    }
    byte_length = str(sys.getsizeof(slack_data))
    headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
    response = requests.post(SLACKURL, data=json.dumps(slack_data), headers=headers)