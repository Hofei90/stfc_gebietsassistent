import discord
import toml
import sys
import asyncio

CONFIG = toml.load("config.toml")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


async def get_role_id(ctx, role_name):
    for role in ctx.guild.roles:
        if role.name == role_name:
            return role.mention
    raise ValueError(f"❌ Discord-Rolle '{role_name}' nicht gefunden.")


def search_work_channel(work_channel_name):
    for channel in client.get_all_channels():
        if str(channel) == work_channel_name:
            return client.get_channel(channel.id)
    return None


async def send_reminder(text):
    workchannel = search_work_channel(CONFIG["channel"])
    if workchannel is None:
        print("❌ Discord-Kanal nicht gefunden:", CONFIG["channel"])
        await client.close()
        return

    try:
        role = await get_role_id(workchannel, CONFIG["role"])
    except ValueError as e:
        print(str(e))
        await workchannel.send("⚠️ Fehler: Die konfigurierte Rolle wurde nicht gefunden.")
        await client.close()
        return

    await workchannel.send(f"{role}: {text}")
    await client.close()


@client.event
async def on_ready():
    try:
        await send_reminder(sys.argv[1])
    finally:
        loop = asyncio.get_event_loop()
        loop.stop()  # explizit Event-Loop stoppen bei mehreren Tasks


def main():
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(client.start(CONFIG["dc_token"]))
        loop.run_forever()
    except KeyboardInterrupt:
        print("Abbruch durch Benutzer")
    finally:
        loop.run_until_complete(client.close())
        loop.close()


if __name__ == "__main__":
    main()
