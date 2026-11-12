import asyncio
import datetime
import os
import re
import shutil
import subprocess

import discord
import toml
import tomlkit
from discord import app_commands

import utils

CONFIG = toml.load("config.toml")
DATA_FILE = "data.toml"
LOG_FILE = "gebietsassistent_admin.log"

MAX_NAME_LENGTH = 50
MAX_MESSAGE_LENGTH = 1900

GUILD = discord.Object(id=int(CONFIG["guild_id"]))
WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WEEKDAY_CHOICES = [app_commands.Choice(name=day, value=day) for day in WEEKDAYS]
NO_PINGS = discord.AllowedMentions.none()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
write_lock = asyncio.Lock()


# ---------- Protokoll ----------

def write_log(interaction, text):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    text = text.replace("\n", " | ")
    line = f"{now} | {interaction.user} ({interaction.user.id}) | {text}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


# ---------- Berechtigung ----------

def is_allowed(interaction):
    if interaction.guild_id != GUILD.id:
        return False
    if CONFIG.get("admin_channel") and str(interaction.channel) != CONFIG["admin_channel"]:
        return False
    if not isinstance(interaction.user, discord.Member):
        return False
    for role in interaction.user.roles:
        if role.name == CONFIG["admin_role"]:
            return True
    return False


async def check_allowed(interaction):
    if is_allowed(interaction):
        return True
    write_log(interaction, f"VERWEIGERT: /{interaction.command.name}")
    await answer(interaction, "⛔ Dazu hast du keine Berechtigung.")
    return False


async def answer(interaction, text):
    if len(text) > MAX_MESSAGE_LENGTH:
        text = text[:MAX_MESSAGE_LENGTH] + "\n…"
    await interaction.response.send_message(text, ephemeral=True, allowed_mentions=NO_PINGS)


# ---------- Eingabeprüfung ----------

def check_text(text, field, max_length):
    text = text.strip()
    if not text:
        raise ValueError(f"'{field}' darf nicht leer sein.")
    if len(text) > max_length:
        raise ValueError(f"'{field}' darf höchstens {max_length} Zeichen lang sein.")
    for char in text:
        if not char.isprintable():
            raise ValueError(f"'{field}' enthält unerlaubte Zeichen (z. B. Zeilenumbruch).")
    return text


def check_time(time_str):
    time_str = time_str.strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", time_str)
    if match is None:
        raise ValueError("Die Uhrzeit muss im Format HH:MM angegeben werden (UTC).")
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise ValueError("Die Uhrzeit ist ungültig (Stunde 0-23, Minute 0-59).")
    return f"{hour}:{minute:02d}"


def check_date(weekday, time_str):
    if weekday not in WEEKDAYS:
        raise ValueError("Unbekannter Wochentag.")
    date = f"{weekday} {check_time(time_str)}"
    utils.get_target_datetime(date)  # gleiche Berechnung wie im Rest des Programms
    return date


def find_territory(territories, system):
    for territory in territories:
        if territory["system"].lower() == system.strip().lower():
            return territory
    return None


# ---------- data.toml lesen und sicher schreiben ----------

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return tomlkit.parse(file.read())


def save_data(data):
    text = tomlkit.dumps(data)

    # Gegenprobe mit der gleichen Bibliothek, die der Rest des Programms nutzt
    check = toml.loads(text)
    for territory in check["territories"]:
        utils.get_target_datetime(territory["date"])

    tmp_file = DATA_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as file:
        file.write(text)
        file.flush()
        os.fsync(file.fileno())

    shutil.copy2(DATA_FILE, DATA_FILE + ".bak")
    os.replace(tmp_file, DATA_FILE)


def restart_control():
    command = CONFIG.get("restart_command")
    if not command:
        return "ℹ️ Kein `restart_command` in config.toml eingetragen."
    try:
        result = subprocess.run(command, check=False, timeout=60, capture_output=True, text=True)
    except (OSError, subprocess.TimeoutExpired) as e:
        print("❌ Neustart fehlgeschlagen:", e)
        return "⚠️ Der Neustart des Gebietsassistenten ist fehlgeschlagen."
    if result.returncode != 0:
        print("❌ Neustart fehlgeschlagen:", result.stderr)
        return "⚠️ Der Neustart des Gebietsassistenten ist fehlgeschlagen."
    return "🔄 Gebietsassistent wurde neu gestartet."


async def change_data(interaction, change):
    """change(data) ändert die Daten und gibt einen Text für Antwort und Protokoll zurück."""
    async with write_lock:
        try:
            data = load_data()
            text = change(data)
            save_data(data)
        except ValueError as e:
            await answer(interaction, f"❌ {e}")
            return
        except Exception as e:
            print("❌ Fehler beim Speichern:", repr(e))
            await answer(interaction, "❌ Fehler beim Speichern, data.toml wurde nicht verändert.")
            return

        write_log(interaction, text)
    await answer(interaction, f"✅ {text}\nℹ️ Wirksam erst nach /gebiet_neustart.")


def territory_text(territory):
    status = "🟢 aktiv" if territory["priority"] else "⚪ inaktiv"
    system = discord.utils.escape_markdown(str(territory["system"]))
    return (f"**{system}** ({status}) - Kat. {territory['kategorie']}, "
            f"{territory['date']} UTC")


def table_text(territories):
    # Jede Zeile beginnt mit genau einem Emoji, damit die Spalten trotzdem untereinander stehen
    header = ["📋", "Status", "System", "Kat", "Termin (UTC)"]
    rows = []
    for territory in territories:
        rows.append(["🟢" if territory["priority"] else "⚪",
                     "aktiv" if territory["priority"] else "inaktiv",
                     str(territory["system"]),
                     str(territory["kategorie"]),
                     str(territory["date"])])

    widths = [len(title) for title in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def line(cells):
        # Emoji vorne und letzte Spalte nicht auffüllen
        middle = " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells[1:-1], start=1))
        return f"{cells[0]} {middle} | {cells[-1]}".replace("`", "'")

    lines = [line(header)]
    for row in rows:
        lines.append(line(row))

    # Codeblock darf nicht abgeschnitten werden, sonst fehlt das schließende ```
    text = ""
    for index, row_text in enumerate(lines):
        if len(text) + len(row_text) + 20 > MAX_MESSAGE_LENGTH:
            text += f"… ({len(lines) - index} weitere)\n"
            break
        text += row_text + "\n"
    return f"```\n{text}```"


async def system_autocomplete(interaction, current):
    if not is_allowed(interaction):
        return []
    choices = []
    for territory in toml.load(DATA_FILE)["territories"]:
        if current.lower() in territory["system"].lower():
            choices.append(app_commands.Choice(name=territory["system"], value=territory["system"]))
    return choices[:25]


# ---------- Befehle ----------

def sort_by_date(territory):
    weekday, time_str = territory["date"].split()
    hour, minute = map(int, time_str.split(":"))
    return WEEKDAYS.index(weekday), hour, minute


def sort_by_system(territory):
    return territory["system"].lower()


@tree.command(name="gebiet_liste", description="Alle Gebiete anzeigen", guild=GUILD)
@app_commands.default_permissions()
@app_commands.describe(sortierung="Sortierung der Liste (Standard: Wochentag und Uhrzeit)")
@app_commands.choices(sortierung=[app_commands.Choice(name="Wochentag und Uhrzeit", value="termin"),
                                  app_commands.Choice(name="Systemname (alphabetisch)", value="system")])
async def gebiet_liste(interaction: discord.Interaction, sortierung: app_commands.Choice[str] = None):
    if not await check_allowed(interaction):
        return
    territories = toml.load(DATA_FILE)["territories"]
    if sortierung is not None and sortierung.value == "system":
        territories = sorted(territories, key=sort_by_system)
    else:
        territories = sorted(territories, key=sort_by_date)
    if not territories:
        await answer(interaction, "Keine Gebiete vorhanden.")
        return
    await answer(interaction, table_text(territories))


@tree.command(name="gebiet_neu", description="Neues Gebiet anlegen", guild=GUILD)
@app_commands.default_permissions()
@app_commands.describe(uhrzeit="Uhrzeit in UTC, z. B. 14:00", aktiv="Erinnerung aktiv (priority)")
@app_commands.choices(wochentag=WEEKDAY_CHOICES)
async def gebiet_neu(interaction: discord.Interaction,
                     system: str,
                     kategorie: app_commands.Range[int, 1, 10],
                     wochentag: app_commands.Choice[str],
                     uhrzeit: str,
                     aktiv: bool):
    if not await check_allowed(interaction):
        return

    def change(data):
        name = check_text(system, "system", MAX_NAME_LENGTH)
        if find_territory(data["territories"], name) is not None:
            raise ValueError(f"Das System '{name}' gibt es bereits.")
        territory = tomlkit.table()
        territory["system"] = name
        territory["kategorie"] = kategorie
        territory["date"] = check_date(wochentag.value, uhrzeit)
        territory["priority"] = 1 if aktiv else 0
        data["territories"].append(territory)
        return f"Gebiet angelegt: {territory_text(territory)}"

    await change_data(interaction, change)


@tree.command(name="gebiet_aendern", description="Bestehendes Gebiet ändern", guild=GUILD)
@app_commands.default_permissions()
@app_commands.describe(uhrzeit="Uhrzeit in UTC, z. B. 14:00")
@app_commands.choices(wochentag=WEEKDAY_CHOICES)
@app_commands.autocomplete(system=system_autocomplete)
async def gebiet_aendern(interaction: discord.Interaction,
                         system: str,
                         kategorie: app_commands.Range[int, 1, 10] = None,
                         wochentag: app_commands.Choice[str] = None,
                         uhrzeit: str = None):
    if not await check_allowed(interaction):
        return

    def change(data):
        territory = find_territory(data["territories"], system)
        if territory is None:
            raise ValueError(f"Das System '{system}' gibt es nicht.")
        old_text = territory_text(territory)
        if kategorie is not None:
            territory["kategorie"] = kategorie
        if wochentag is not None or uhrzeit is not None:
            old_weekday, old_time = str(territory["date"]).split()
            new_weekday = wochentag.value if wochentag is not None else old_weekday
            new_time = uhrzeit if uhrzeit is not None else old_time
            territory["date"] = check_date(new_weekday, new_time)
        return f"Gebiet geändert:\nalt: {old_text}\nneu: {territory_text(territory)}"

    await change_data(interaction, change)


async def set_priority(interaction, system, priority):
    if not await check_allowed(interaction):
        return

    def change(data):
        territory = find_territory(data["territories"], system)
        if territory is None:
            raise ValueError(f"Das System '{system}' gibt es nicht.")
        territory["priority"] = priority
        return f"Gebiet {'aktiviert' if priority else 'deaktiviert'}: {territory_text(territory)}"

    await change_data(interaction, change)


@tree.command(name="gebiet_aktivieren", description="Erinnerung für ein Gebiet aktivieren", guild=GUILD)
@app_commands.default_permissions()
@app_commands.autocomplete(system=system_autocomplete)
async def gebiet_aktivieren(interaction: discord.Interaction, system: str):
    await set_priority(interaction, system, 1)


@tree.command(name="gebiet_deaktivieren", description="Erinnerung für ein Gebiet deaktivieren", guild=GUILD)
@app_commands.default_permissions()
@app_commands.autocomplete(system=system_autocomplete)
async def gebiet_deaktivieren(interaction: discord.Interaction, system: str):
    await set_priority(interaction, system, 0)


@tree.command(name="gebiet_neustart", description="Gebietsassistent neu starten, damit Änderungen wirksam werden", guild=GUILD)
@app_commands.default_permissions()
async def gebiet_neustart(interaction: discord.Interaction):
    if not await check_allowed(interaction):
        return
    async with write_lock:
        await interaction.response.defer(ephemeral=True, thinking=True)
        text = await asyncio.to_thread(restart_control)
        write_log(interaction, f"/gebiet_neustart: {text}")
    await interaction.followup.send(text, ephemeral=True, allowed_mentions=NO_PINGS)


# ---------- Start ----------

@client.event
async def setup_hook():
    await tree.sync(guild=GUILD)


@client.event
async def on_ready():
    print(f"✅ Admin-Bot angemeldet als {client.user}")


def main():
    client.run(CONFIG["dc_token"])


if __name__ == "__main__":
    main()
