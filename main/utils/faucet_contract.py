from main.apps import LOGGER
from main.js.runner import ScriptFunctions
from main.models import FaucetContract

from .crypto import get_tx_hash
from .watchtower_api import Watchtower

def compile_contract(passcode:str, payout_satoshis:int, owner_address:str, network:str):
    return ScriptFunctions.compileFaucetContract(dict(
        params=dict(
            passcode=passcode,
            payoutSats=payout_satoshis,
            ownerAddress=owner_address,
        ),
        options=dict(network=network),
    ))

def compile_obj(obj:FaucetContract):
    return ScriptFunctions.compileFaucetContract(obj.contract_opts)

def faucet_claim(obj:FaucetContract, recipient:str, passcode:str, broadcast=True):
    LOGGER.debug(f"Claim | {obj} | {recipient}")
    wt_api = Watchtower(network = obj.network)
    utxos = wt_api.get_bch_utxos(obj.address, parse="cashscript")

    utxo = None
    for _utxo in utxos:
        if _utxo["satoshis"] >= obj.payout_satoshis + obj.claim_tx_fee:
            utxo = _utxo
            break

    if not utxo:
        return False, "Not enough funds to claim"

    result = ScriptFunctions.faucetClaim(dict(
        contractOpts=obj.contract_opts,
        utxo=utxo,
        recipient=recipient,
        passcode=passcode,
    ))

    if not result["success"]:
        return False, result.get("error", "Failed to create transaction")

    transaction = result["transaction"]
    txid = get_tx_hash(transaction)
    try:
        LOGGER.debug(f"Broadcasting claim TX | {transaction}")
        wt_api.broadcast(transaction)
    except Watchtower.WatchtowerException as exception:
        return False, f"{exception}"

    return True, txid


def sweep_faucet(obj:FaucetContract, wif:str, recipient:str=None):
    wt_api = Watchtower(network = obj.network)
    utxos = wt_api.get_bch_utxos(obj.address, parse="cashscript")

    result = ScriptFunctions.faucetSweep(dict(
        contractOpts=obj.contract_opts,
        utxos=utxos,
        recipient=recipient,
        wif=wif,
    ))

    if not result["success"]:
        return False, result.get("error", "Failed to create sweep transaction")

    transaction = result["transaction"]
    txid = get_tx_hash(transaction)
    try:
        wt_api.broadcast(transaction)
    except Watchtower.WatchtowerException as exception:
        return False, f"{exception}"

    return True, txid
