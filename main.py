import discord
import os 
from discord.ext import commands
import yaml
import asyncio
import logging
import sys

# Set logging config
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)

# Load config file
with open("./config.yml", "r", encoding="utf-8") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# Set bot intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot
bot = commands.Bot(
    command_prefix=config["Prefix"], description="Stock information bot", case_insensitive=True, intents=intents)

@bot.event
async def on_ready():
   # Display running status and set activity
   print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
   await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["Watching Status"]))


# Load cogs 
async def load_extensions():
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

# Run bot
async def main():
    async with bot:
        await load_extensions()
        await bot.start(config["Token"])

asyncio.run(main())