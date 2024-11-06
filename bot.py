from discord.ext import commands
from discord import Intents
from config import BotConfig

configuration = BotConfig()

intents = Intents.default()
intents.members = True

# create bot instance
bot = commands.Bot(command_prefix=configuration.COMMAND_PREFIX, intents=intents)


@bot.event
async def on_ready():
    await bot.load_extension("cogs.finance_cog")
    await bot.tree.sync()
    print(f"{bot.user.name} has connected to Discord!")


# welcome message
@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(
            f"Welcome {member.mention}! I am {bot.user.name}. I can help you with financial data. Use the slash commands to interact with me."
        )


bot.run(configuration.DISCORD_TOKEN)
