import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
import os
import asyncio
import sqlite3
import requests

import discord
from discord.ext import commands
from colorama import Fore, Style, init

# =====================
# BASIC SETUP
# =====================

init(autoreset=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

VERSION_URL = "https://raw.githubusercontent.com/Reloisback/Whiteout-Survival-Discord-Bot/refs/heads/main/autoupdateinfo.txt"

# =====================
# BOT CLASS
# =====================

class CustomBot(commands.Bot):
    async def on_error(self, event_name, *args, **kwargs):
        if event_name == "on_interaction":
            error = sys.exc_info()[1]
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
        await super().on_error(event_name, *args, **kwargs)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return
        await super().on_command_error(ctx, error)

# =====================
# INTENTS & BOT
# =====================

intents = discord.Intents.default()
intents.message_content = True

bot = CustomBot(command_prefix='/', intents=intents)

# =====================
# DB SETUP
# =====================

if not os.path.exists("db"):
    os.makedirs("db")
    print(Fore.GREEN + "db folder created" + Style.RESET_ALL)

databases = {
    "conn_alliance": "db/alliance.sqlite",
    "conn_giftcode": "db/giftcode.sqlite",
    "conn_changes": "db/changes.sqlite",
    "conn_users": "db/users.sqlite",
    "conn_settings": "db/settings.sqlite",
}

connections = {name: sqlite3.connect(path) for name, path in databases.items()}
print(Fore.GREEN + "Database connections have been successfully established." + Style.RESET_ALL)

def create_tables():
    with connections["conn_changes"] as c:
        c.execute("""CREATE TABLE IF NOT EXISTS nickname_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fid INTEGER,
            old_nickname TEXT,
            new_nickname TEXT,
            change_date TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS furnace_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fid INTEGER,
            old_furnace_lv INTEGER,
            new_furnace_lv INTEGER,
            change_date TEXT
        )""")

    with connections["conn_settings"] as c:
        c.execute("""CREATE TABLE IF NOT EXISTS botsettings (
            id INTEGER PRIMARY KEY,
            channelid INTEGER,
            giftcodestatus TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            is_initial INTEGER
        )""")

    with connections["conn_users"] as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY,
            nickname TEXT,
            furnace_lv INTEGER DEFAULT 0,
            kid INTEGER,
            stove_lv_content TEXT,
            alliance TEXT
        )""")

    with connections["conn_giftcode"] as c:
        c.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
            giftcode TEXT PRIMARY KEY,
            date TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_giftcodes (
            fid INTEGER,
            giftcode TEXT,
            status TEXT,
            PRIMARY KEY (fid, giftcode)
        )""")

    with connections["conn_alliance"] as c:
        c.execute("""CREATE TABLE IF NOT EXISTS alliancesettings (
            alliance_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            interval INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS alliance_list (
            alliance_id INTEGER PRIMARY KEY,
            name TEXT
        )""")

    print(Fore.GREEN + "All tables checked." + Style.RESET_ALL)

create_tables()

# =====================
# VERSION TABLE
# =====================

def setup_version_table():
    with sqlite3.connect("db/settings.sqlite") as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS versions (
            file_name TEXT PRIMARY KEY,
            version TEXT,
            is_main INTEGER DEFAULT 0
        )""")
        conn.commit()
        print(Fore.GREEN + "Version table created successfully." + Style.RESET_ALL)

setup_version_table()

# =====================
# UPDATE CHECK
# =====================

async def check_and_update_files():
    try:
        response = requests.get(VERSION_URL, timeout=10)
        if response.status_code != 200:
            print(Fore.YELLOW + "Version check skipped (GitHub unreachable)" + Style.RESET_ALL)
            return
    except Exception as e:
        print(Fore.YELLOW + f"Version check error: {e}" + Style.RESET_ALL)
        return

# =====================
# LOAD COGS
# =====================

async def load_cogs():
    cogs = [
        "olddb",
        "control",
        "alliance",
        "alliance_member_operations",
        "bot_operations",
        "logsystem",
        "support_operations",
        "gift_operations",
        "changes",
        "w",
        "wel",
        "other_features",
        "bear_trap",
        "id_channel",
        "backup_operations",
        "bear_trap_editor",
    ]

    for cog in cogs:
        await bot.load_extension(f"cogs.{cog}")

# =====================
# EVENTS
# =====================

class CustomBot(commands.Bot):
    async def setup_hook(self):
        await load_cogs()
        await self.tree.sync()
        print(Fore.GREEN + "Slash commands synced." + Style.RESET_ALL)

    async def on_error(self, event_name, *args, **kwargs):
        if event_name == "on_interaction":
            error = sys.exc_info()[1]
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
        await super().on_error(event_name, *args, **kwargs)

# =====================
# MAIN
# =====================

async def main():
    await check_and_update_files()
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
