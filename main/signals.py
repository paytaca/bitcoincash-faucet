from django.db.models.signals import post_save
from django.dispatch import receiver

from main.apps import LOGGER
from main.models import FaucetContract
from main.utils.watchtower_api import Watchtower

@receiver(post_save, sender=FaucetContract)
def post_save_faucet_contract(sender, instance=None, created=False, **kwargs):
    if not created: return

    wt_api = Watchtower(network=instance.network)
    success, error = wt_api.subscribe_address(instance.address)

    if success:
        LOGGER.info(f"Subscribed new faucet {instance} | Success => {success}")
        # to not re-trigger the signals
        FaucetContract.objects.filter(pk=instance.pk).update(subscribed=True)
    else:
        LOGGER.warn(f"Failed to subcribe new faucet {instance} | Error => {error}")
