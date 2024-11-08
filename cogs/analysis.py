from discord.ext import commands
from discord import app_commands, Embed
import yfinance as yf


# Import utils
from cogs.utils import is_valid_ticker

# Import constants
from constants import EMBED_COLOR_PRIMARY, FOOTER_TEXT


class AnalysisCog(commands.Cog):
    """
    A cog for fetching stock data using the Yahoo Finance API.
    This cog provides basic commands aimed at ticker analysis such as bollinger.
    """

    def __init__(self, bot, session):
        self.bot = bot
        # Use a single session across the class to cache and limit requests
        self.session = session

    @app_commands.command(
        name="bollinger",
        description="Calculate Bollinger Bands for a given ticker symbol.",
    )
    async def bollinger(self, interaction, ticker: str):
        """Fetch Bollinger Bands for the specified ticker."""
        await interaction.response.defer()
        if not is_valid_ticker(ticker, session=self.session):
            await interaction.followup.send(
                f"The ticker '{ticker}' is not valid. Please check and try again."
            )
            return

        try:
            data = self.get_bollinger_bands(ticker)
            await interaction.followup.send(f"Bollinger Bands for {ticker}:\n{data}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    def get_bollinger_bands(self, ticker):
        """Calculate Bollinger Bands for the specified ticker."""
        # Fetch historical data
        stock_data = yf.download(ticker, period="1mo", interval="1d")

        # Calculate the rolling mean and rolling standard deviation
        stock_data["MA"] = stock_data["Close"].rolling(window=20).mean()
        stock_data["STD"] = stock_data["Close"].rolling(window=20).std()

        # Calculate Bollinger Bands
        stock_data["Upper Band"] = stock_data["MA"] + (stock_data["STD"] * 2)
        stock_data["Lower Band"] = stock_data["MA"] - (stock_data["STD"] * 2)

        # Return the most recent values
        latest_data = stock_data[["Close", "Upper Band", "Lower Band"]].tail(1)
        return latest_data.to_string(index=False)


# Called when the cog is loaded
async def setup(bot):
    await bot.add_cog(AnalysisCog(bot, bot.session))
