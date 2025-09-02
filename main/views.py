import json
from django.utils import timezone
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse

from main.apps import LOGGER
from main.models import FaucetClaim, FaucetContract
from main.forms import FaucetForm
from main.utils.faucet_contract import faucet_claim, update_faucet_balance

# Create your views here.
def get_client_ip(request):
    # basic approach; ensure your reverse proxy sets X-Forwarded-For correctly
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class FaucetClaimView(View):
    def get_recent_claims(self):
        return FaucetClaim.objects.order_by("-created_at")[:10]

    def get(self, request, *args, **kwargs):
        form = FaucetForm()
        ctx = dict(
            form=form,
            recent=self.get_recent_claims(),
        )
        return render(request, "main/claim.html", ctx)

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        form = FaucetForm(request.POST)
        ctx = dict(form=form, recent=self.get_recent_claims())

        if not form.is_valid():
            return render(request, "main/claim.html", ctx)

        address = form.cleaned_data['address']
        passcode = form.cleaned_data['passcode']
        faucet = form.cleaned_data['faucet']

        one_day_ago = timezone.now() - timezone.timedelta(days=1)
        recent_claims = faucet.claims.filter(ip=ip, created_at__gte=one_day_ago)
        if recent_claims.exists():
            form.add_error(None, "Already claimed in the last 24 hours, come back again later")
            return render(request, "main/claim.html", ctx)

        success, error_or_txid = faucet_claim(faucet, address, passcode, broadcast=True)

        if not success:
            form.add_error(None, f"Claim failed: {error_or_txid}")
            return render(request, "main/claim.html", ctx)

        faucet_request = FaucetClaim.objects.create(
            faucet=faucet,
            network=faucet.network,
            recipient=address, satoshis=faucet.payout_satoshis,
            ip=ip,
            txid=error_or_txid,
        )
        faucet.claim_count += 1
        faucet.save()

        try:
            LOGGER.info(f"UPDATING BALANCE | {faucet}")
            update_faucet_balance(faucet)
        except Exception as exception:
            LOGGER.exception(exception)

        ctx["form"] = FaucetForm()
        ctx["success"] = f"Sent {faucet_request.satoshis / 10e8:.8f} BCH to {faucet_request.recipient}"

        return render(request, "main/claim.html", ctx)


class WatchtowerWebhookView(View):
    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
        except json.JSONDecodeError as exception:
            LOGGER.debug(f"Invalid JSON from webhook, attempting POST data instead | {request.body}")
            json_data = request.POST.dict()

        LOGGER.info(f"RECEIVED WEBHOOK | {json.dumps(json_data, indent=2)}")

        address = json_data.get("address")
        if address:
            LOGGER.info(f"GOT ADDRESS FROM WEBHOOK | {address}")
            faucet = FaucetContract.objects.filter(address=address).first()
            if faucet:
                LOGGER.info(f"UPDATING BALANCE | {faucet}")
                update_faucet_balance(faucet)

        return JsonResponse(dict(acknowledged=True))
