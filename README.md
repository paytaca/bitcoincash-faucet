# Bitcoin Cash Faucet

A simple Bitcoin Cash (BCH) faucet built using [CashScript](cashscript.org) for smart contract-powered transactions.

## How It Works
1. **Create a FaucetContract in Django admin**  
   - Go to `Admin › Home › Main › Faucet contracts › Add faucet contract`
   - Select the network
   - The following fields must be a unique set for the smart contracts parameters:
     - Set a passcode (around 10 characters long)
     - Set the payout amount in satoshis
     - Set an owner address. This is for sweeping the faucet contract's funds
   - Set the max claim count limit

2. **Fund the contract**  
   - Send BCH to the contract.
   - You can send exact amount based on `max claim count` and `payout satoshis` set for the contract.
        ```
            claim_tx_fee_sats = 300
            sats_to_send = (payout_satoshis + claim_tx_fee_sats) * max_claim_count
            bch_to_send = sats_to_send / 10 ** 8
        ```

3. **Test claiming**  
   - Go to `/claim` page
   - Input receipient address, passcode, and select network. Must be a cashaddress with the appropirate network selected
   - Claiming is limited per IP address. There is a 24 hour cooldown to allow claiming again from the same IP address.

4. **Sweep remaining funds from contract**
    - Go to `Admin › Home › Main › Faucet contracts › Faucet details` and press `SWEEP` button beside `HISTORY` button
    - Input recipient & wif
    - Submit form
