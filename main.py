from discord.ext import commands
from discord import Intents
from config import BotConfig

# Libraries for creating session
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


# Create and configure the session
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    def __init__(self):
        limiter = Limiter(RequestRate(2, Duration.SECOND * 5))
        backend = SQLiteCache("yfinance.cache")
        super().__init__(
            limiter=limiter, bucket_class=MemoryQueueBucket, backend=backend
        )


session = CachedLimiterSession()

# Bot configuration
configuration = BotConfig()

intents = Intents.default()
intents.members = True

# create bot instance
bot = commands.Bot(command_prefix=configuration.COMMAND_PREFIX, intents=intents)
bot.session = session


@bot.event
async def on_ready():
    # Pass session to the cog when loading it
    await bot.load_extension("cogs.stocks")
    await bot.load_extension("cogs.analysis")
    await bot.tree.sync()
    print(f"{bot.user.name} has connected to Discord!")


@bot.event
async def on_shutdown():
    # Close the session when the bot is closed
    session.close()
    print("Session closed!")


bot.run(configuration.DISCORD_TOKEN)

# # welcome message
# @bot.event
# async def on_member_join(member):
#     channel = member.guild.system_channel
#     if channel:
#         await channel.send(
#             f"Welcome {member.mention}! I am {bot.user.name}. I can help you with financial data. Use the slash commands to interact with me."
#         )
