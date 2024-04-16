import discord
import toml
import sys


CONFIG = toml.load("config.toml")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def get_role_id(ctx, role_name):
    for role in ctx.guild.roles:
        if role.name == role_name:
            return role.mention


def search_work_channel(work_channel_name):
    channels = client.get_all_channels()
    work_channel = None
    for channel in channels:
        if str(channel) == work_channel_name:
            work_channel = client.get_channel(channel.id)
            break
    return work_channel


async def send_reminder(text):
    workchannel = search_work_channel(CONFIG["channel"])
    role = await get_role_id(workchannel, CONFIG["role"])
    await workchannel.send(f"{role}: {text}")
    exit(0)


@client.event
async def on_ready():
    await send_reminder(sys.argv[1])


if __name__ == "__main__":
    client.run(toml.load("config.toml")["dc_token"])