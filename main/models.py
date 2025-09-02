from django.db import models

# Create your models here.
class Network(models.TextChoices):
    mainnet = "mainnet"
    chipnet = "chipnet"

class FaucetContract(models.Model):
    address = models.CharField(max_length=75, unique=True, db_index=True)
    network = models.CharField(max_length=15, choices=Network.choices)

    passcode = models.CharField(max_length=10)
    payout_satoshis = models.PositiveIntegerField()
    owner_address = models.CharField(max_length=75)

    claim_count = models.PositiveIntegerField(default=0)
    max_claim_count = models.PositiveIntegerField(null=True, blank=True)

    subscribed = models.BooleanField(default=False, help_text="If subscribed to watchtower")
    balance_satoshis = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Faucet#{self.id} <{self.address}>"

    @property
    def claim_tx_fee(self):
        return 300

    @property
    def contract_opts(self):
        return dict(
            params=dict(
                passcode=self.passcode,
                payoutSats=self.payout_satoshis,
                ownerAddress=self.owner_address,
            ),
            options=dict(network=self.network),
        )


class FaucetClaim(models.Model):
    faucet = models.ForeignKey(
        FaucetContract, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="claims",
    )

    network = models.CharField(max_length=15, choices=Network.choices)
    txid = models.CharField(max_length=64)
    recipient = models.CharField(max_length=75)
    satoshis = models.PositiveIntegerField()

    ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def amount_bch(self):
        return self.satoshis / 10e8

    @property
    def tx_link(self):
        if self.network == "chipnet":
            return f"https://chipnet.bch.ninja/tx/{self.txid}"
        return f"https://explorer.bch.ninja/tx/{self.txid}"
