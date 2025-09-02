import json
import requests
from urllib.parse import urljoin
from bitcash.network.meta import Unspent

from django.conf import settings


class WatchtowerException(Exception):
    pass

class Watchtower:
    WatchtowerException = WatchtowerException

    def __init__(self, network="mainnet"):
        self._network = network
        self._session = requests.Session()
        self._session.headers["Accept"] = "application/json"

    @property
    def base_url(self):
        try:
            return settings.WATCHTOWER_BASE_URLS[self._network]
        except (TypeError, KeyError):
            return None

    def generate_url(self, path):
        base_url = self.base_url
        if not base_url or not isinstance(base_url, str): return
        if not isinstance(path, str): return

        # this ensures the urlpath in base_url is not overwritten in urljoin
        if not base_url.endswith("/"): base_url += "/"
        if path.startswith("/"): path = path[1:]

        return urljoin(base_url, path)

    def _request(self, method, url, *args, **kwargs):
        full_url = self.generate_url(url)
        if not full_url: BCMRException("Unable to construct api url")
        return self._session.request(method.upper(), full_url, *args, **kwargs)

    @classmethod
    def parse_as_bitcash_utxo(cls, data:dict):
        assert isinstance(data, dict)
        if not data: return None

        return Unspent(
            data["value"],  # amount
            0,              # confirmations
            "",             # script
            data["txid"],   # txid
            data["vout"],   # txindex
            category_id = data.get("tokenid"),
            nft_capability = data.get("capability"),
            nft_commitment = data.get("commitment"),
            token_amount = data.get("amount"),
        )

    @classmethod
    def parse_as_cashscript_utxo(cls, data:dict):
        assert isinstance(data, dict)
        if not data: return None

        response = dict(
            txid=data["txid"],
            vout=data["vout"],
            satoshis=data["value"],
        )

        if data.get("is_cashtoken"):
            response["token"] = dict(
                category=data["tokenid"],
                amount=data["amount"],
            )
            if data.get("capability"):
                response["token"]["nft"] = dict(
                    capability=data["capability"],
                    commitment=data["commitment"],
                )

        return response

    def parse_utxos_response(self, response, parse=None):
        if not response.ok:
            raise WatchtowerException(f"Failed to fetch utxos. Status: {response.status_code}")
        # raise Exception(f"response | {response.content}")
        try:
            response_data = response.json()
        except json.JsonDecodeError:
            raise WatchtowerException(f"Invalid utxos response: {response.content} ")

        if parse == "bitcash":
            return [self.parse_as_bitcash_utxo(utxo) for utxo in response_data["utxos"]]
        elif parse == "cashscript":
            return [self.parse_as_cashscript_utxo(utxo) for utxo in response_data["utxos"]]

        return response_data

    def get_balance(self, address):
        response = self._request("get", f"balance/bch/{address}/")
        if not response.ok:
            raise WatchtowerException(response.content)
        response_data = response.json()
        return response_data

    def get_bch_utxos(self, address, confirmed=None, parse=None):
        params = {}
        if isinstance(confirmed, bool):
            params["confirmed"] = str(params).lower()

        response = self._request("get", f"utxo/bch/{address}/")
        return self.parse_utxos_response(response, parse=parse)

    def get_cashtoken_utxos(self, tokenaddress, category_id=None, confirmed=None, parse=False):
        url_path = f"utxo/ct/{tokenaddress}/"

        # this option doesn't work yet, might not want to use it for now
        if category_id: url_path += f"{category_id}/"

        params = {}
        if isinstance(confirmed, bool):
            params["confirmed"] = str(params).lower()

        response = self._request("get", url_path)
        return self.parse_utxos_response(response, parse=parse)

    def transaction_outputs(self, **kwargs):
        return self._request("get", "transactions/outputs/", params=kwargs).json()

    def get_spending_txid(self, txid:str, vout:int):
        params = { "txid": txid, "index": str(int(vout)), "limit": 1 }
        response_data = self._request("get", "transactions/outputs/", params=params).json()

        results = response_data.get("results")
        if not isinstance(results, list) or not len(results):
            return

        return results[0]["spending_txid"]

    def broadcast(self, tx_hex):
        data = { "transaction": tx_hex }
        response = self._request("post", "broadcast/", data=data)
        response_data = response.json()

        if not response_data.get("success"):
            raise WatchtowerException(response_data.get("error") or response_data)

        return response_data

    def verify_transaction(self, tx_hex):
        data = { "transaction": tx_hex }

        response = self._request("post", "stablehedge/test-utils/test_mempool_accept/", data=data)
        response_data = response.json()

        if not response_data.get("success"):
            raise WatchtowerException(response_data.get("error") or response_data)

        return response_data

    def subscribe_address(self, address, webhook_url:str=None):
        project_id = settings.WATCHTOWER_PROJECT_ID
        if self._network == "chipnet":
            project_id = settings.WATCHTOWER_CHIPNET_PROJECT_ID
        data = dict(address=address, project_id=project_id)
        if webhook_url:
            data["webhook_url"] = webhook_url

        response = self._request("post", "subscription/", data=data)
        success = response.ok and response.json().get("success")
        error = response.ok and response.json().get("error")
        return success, error
