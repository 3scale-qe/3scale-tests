"""
Provide a small client for interacting with Requestbin.
"""
import xml.etree.ElementTree as Et
import requests


# pylint: disable=too-few-public-methods
class RequestBinClient:
    """
    Requestbin client.

    Note: Contains only methods being used by actual tests.
    """

    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.api_url = f"{self.endpoint}/api/v1/bins"
        self.name = requests.post(self.api_url).json()["name"]
        self.url = f"{self.endpoint}/{self.name}"

    def get_webhook(self, action: str, entity_id: str):
        """
        :return webhook for given action and entity_id
        """

        def xml_find(element, tag):
            result = element.find(tag)
            if result is None:
                return ""
            return result.text

        webhooks = requests.get(f"{self.api_url}/{self.name}/requests").json()
        webhooks = list(filter(lambda x: x["body"] != "", webhooks))
        for webhook in webhooks:
            xml = Et.fromstring(webhook["body"])
            webhook_type = xml_find(xml, ".//type")
            webhook_id = xml_find(xml, f".//{webhook_type}/id")
            webhook_action = xml_find(xml, ".//action")
            if webhook_id == entity_id and webhook_action == action:
                return webhook["body"]
        return None
