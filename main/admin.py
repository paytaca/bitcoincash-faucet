from django.contrib import admin
from django.contrib import messages

from django.urls import path
from django.shortcuts import render, get_object_or_404

from main.models import FaucetContract, FaucetClaim
from main.forms import FaucetContractForm, SweepFaucetContractForm

from main.utils.faucet_contract import sweep_faucet
from main.utils.watchtower_api import Watchtower

# Register your models here.
@admin.register(FaucetContract)
class FaucetContractAdmin(admin.ModelAdmin):
    form = FaucetContractForm

    search_fields = [
        "passcode",
    ]

    list_display = [
        "__str__",
        "passcode",
        "payout_satoshis",
        "owner_address",

        "claim_count",
        "max_claim_count",
    ]

    list_filter = [
        "network",
    ]

    actions = [
        "subscribe_to_watchtower",
    ]
    change_form_template = "admin/faucet_contract/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:contract_id>/sweep/",
                self.admin_site.admin_view(self.sweep_faucet_view),
                name="faucet_contract_sweep",
            ),
        ]
        return custom_urls + urls

    def sweep_faucet_view(self, request, contract_id, *args, **kwargs):
        obj = get_object_or_404(FaucetContract, pk=contract_id)

        if request.method == "POST":
            form = SweepFaucetContractForm(request.POST)
            if form.is_valid():
                wif = form.cleaned_data["wif"]
                recipient = form.cleaned_data.get("recipient")
                success, error_or_txid = sweep_faucet(obj,wif, recipient=recipient)
                if success:
                    messages.success(request, f"Swept funds success: {error_or_txid}")
                    form = SweepFaucetContractForm()
                else:
                    messages.error(request, f"Swept funds error: {error_or_txid}")
        else:
            form = SweepFaucetContractForm()

        return render(
            request,
            "admin/faucet_contract/sweep.html",
            dict(form=form, obj=obj, opts=self.model._meta),
        )

    def subscribe_to_watchtower(self, request, queryset):
        for obj in queryset:
            try:
                wt_api = Watchtower(network=obj.network)
                success, error = wt_api.subscribe_address(obj.address)
                if success:
                    obj.subscribed = True
                    obj.save()
                    messages.success(request, f"Subscribe {obj} success -> {success}")
                else:
                    raise Exception(error)
            except Exception as exception:
                messages.error(request, f"Subscribe {obj} error -> {exception}")


@admin.register(FaucetClaim)
class FaucetClaimAdmin(admin.ModelAdmin):
    search_fields = [
        "faucet__address",
        "txid",
        "recipient",
        "ip",
    ]

    list_display = [
        "__str__",
        "recipient",
        "satoshis",
        "ip",
        "faucet",
        "created_at",
    ]

    list_filter = [
        "network",
        "created_at",
    ]
