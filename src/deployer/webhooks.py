import atexit

import httpx

from deployer import config


discord_client = httpx.Client(base_url="https://discord.com/api/v9")

atexit.register(discord_client.close)

WEBHOOK = (
    config.LoggingConfig.enabled
    and str(config.LoggingConfig.webhook_id) + "/" + config.LoggingConfig.webhook_token
)


def post_alert(
    *, content: str = None, title: str = None, description: str = None, colour: int = None
) -> httpx.Response:
    """Send a message to the discord webhook."""
    if not WEBHOOK:
        return

    global discord_client

    params = {"wait": True}
    data = {}
    embed = {}

    if title:
        embed["title"] = title
    if description:
        embed["description"] = description
    if colour:
        embed["color"] = int(colour)

    if embed:
        data["embeds"] = [embed]

    if content:
        data["content"] = content

    resp = discord_client.post("/webhooks/" + WEBHOOK, params=params, json=data)
    return resp
