# faucet/forms.py
from django import forms
from django.db.models import F
from django.core.exceptions import ValidationError

from captcha.fields import CaptchaField
from cashaddress import convert

from main.models import FaucetContract, Network
from main.utils.faucet_contract import compile_contract

class FaucetContractForm(forms.ModelForm):
    address = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = FaucetContract
        fields = "__all__"

    def clean(self):
        super().clean()

        if self.cleaned_data.get("address"):
            return

        compile_data = compile_contract(
            self.cleaned_data["passcode"],
            self.cleaned_data["payout_satoshis"],
            self.cleaned_data["owner_address"],
            self.cleaned_data["network"],
        )
        self.cleaned_data["address"] = compile_data["address"]


class FaucetForm(forms.Form):
    network = forms.ChoiceField(choices=Network.choices, widget=forms.RadioSelect, label="Network")
    address = forms.CharField(
        max_length=128, label="Your BCH address",
        widget=forms.Textarea(attrs={
            "rows": 2,  # fixed number of rows
            "style": "resize:none;",  # disables manual resizing
        }),
    )
    passcode = forms.CharField(max_length=10)
    captcha = CaptchaField()  # or use ReCAPTCHA field

    def clean(self):
        cleaned_data = super().clean()
        address = cleaned_data["address"]
        passcode = cleaned_data["passcode"]
        network = cleaned_data["network"]

        if not convert.is_valid(address):
            self.add_error("address", "Invalid address")
            return cleaned_data

        if network == "chipnet" and address.startswith("bitcoincash:"):
            self.add_error("address", "Must provide testnet address")
            return cleaned_data
        elif network == "mainnet" and address.startswith("bchtest:"):
            self.add_error("address", "Must provide mainnet address")
            return cleaned_data

        faucet_qs = FaucetContract.objects.filter(
            network=network,
            claim_count__lt=F("max_claim_count"),
        )
        if not faucet_qs:
            raise ValidationError("No claimable faucet")
        faucet = faucet_qs.filter(passcode=passcode).first()
        if not faucet:
            raise ValidationError("Invalid passcode for available faucets")

        cleaned_data["faucet"] = faucet
        return cleaned_data


class SweepFaucetContractForm(forms.Form):
    recipient = forms.CharField(required=False)
    wif = forms.CharField(required=True)
