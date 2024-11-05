from discord.ext import commands
from discord import Intents

from config import BotConfig

# from cogs import my_commands


intents = Intents.default()
intents.members = True


bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")


bot.run(BotConfig().DISCORD_TOKEN)
