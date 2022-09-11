import discord

from discord.ext import commands
import yaml

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
   # Set bot status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=config["Watching Status"]))

try:
    bot.run(config["Token"])
except Exception as e:
    print(f"Fatal error: {e}")