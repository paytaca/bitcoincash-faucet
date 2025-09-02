# faucet/wallet.py
import os
from django.conf import settings
from bitcash import Key, PrivateKeyTestnet
from bitcash.network.meta import Unspent
from decimal import Decimal

from .crypto import get_tx_hash
from .watchtower_api import Watchtower


def send_payout(destination_address:str, amount_satoshis:int, chipnet=True):
    """
    Returns txid on success or raises an exception.
    """
    key = get_wallet(chipnet=chipnet)

    watchtower_api = Watchtower(network="chipnet" if chipnet else "mainnet")
    unspents = watchtower_api.get_bch_utxos(key.address, parse="bitcash")
    for unspent in unspents:
        unspent.script = key.scriptcode.hex()

    outputs = [
        (destination_address, amount_satoshis, "satoshi"),
    ]
    tx_hex = key.create_transaction(outputs, fee=1, unspents=unspents)  # let library estimate fee

    txid = get_tx_hash(tx_hex)
    watchtower_api.broadcast(tx_hex)

    return txid

def get_wallet(chipnet=True):
    wif = settings.FAUCET_WALLET_WIF
    if chipnet:
        return PrivateKeyTestnet(wif)
    return Key(wif)
