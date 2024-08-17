from app.api.v1.managers.db import token_blacklist_manager

from app.core.signals import app_lifecycle


async def on_startup():
    await app_lifecycle.connect(
        receiver=token_blacklist_manager.close,
        sender=token_blacklist_manager.__class__,
        dispatch_uid="token_blacklist_manager_close",
    )


async def on_shutdown():
    await app_lifecycle.send(sender=token_blacklist_manager.__class__)
