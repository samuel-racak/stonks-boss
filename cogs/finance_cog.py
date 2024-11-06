from discord.ext import commands
from discord import app_commands
import yfinance as yf  # To fetch financial data


class FinanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="bollinger",
        description="Calculate Bollinger Bands for a given ticker symbol.",
    )
    async def bollinger(self, interaction, ticker: str):
        """Fetch Bollinger Bands for the specified ticker."""
        await interaction.response.defer()
        if not self.is_valid_ticker(ticker):
            await interaction.followup.send(
                f"The ticker '{ticker}' is not valid. Please check and try again."
            )
            return

        try:
            data = self.get_bollinger_bands(ticker)
            await interaction.followup.send(f"Bollinger Bands for {ticker}:\n{data}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(
        name="price",
        description="Get current price for a given ticker symbol.",
    )
    async def price(self, interaction, ticker: str):
        """Fetch current price for the specified ticker."""
        await interaction.response.defer()
        if not self.is_valid_ticker(ticker):
            await interaction.followup.send(
                f"The ticker '{ticker}' does not exist. Please check and try again."
            )
            return

        try:
            current_price = self.get_current_price(ticker)
            # premarket_price = self.get_premarket_price(ticker)
            await interaction.followup.send(
                f"Current price for {ticker}: {round(current_price, 2)} USD"
            )
            # await interaction.followup.send(
            #     f"Pre-market price for {ticker}: {round(premarket_price, 2)} USD"
            # )

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    def is_valid_ticker(self, ticker):
        """Check if the ticker is valid by attempting to fetch data."""
        try:
            stock_data = yf.Ticker(ticker)
            # If we can fetch info, the ticker is valid
            info = stock_data.info
            return (
                info is not None
                and "symbol" in info
                and info["symbol"] == ticker.upper()
            )
        except Exception as e:
            return False

    def get_bollinger_bands(self, ticker):
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

    def get_current_price(self, ticker):
        # Fetch the current stock price using yfinance
        stock_data = yf.Ticker(ticker)
        price = stock_data.history(period="1d")["Close"].iloc[-1]
        return price

    # def get_premarket_price(self, ticker):
    #     # Fetch the premarket stock price using yfinance
    #     stock_data = yf.Ticker(ticker)
    #     price = stock_data.history(period="1d", interval="1m")["Open"].iloc[-1]
    #     return price


async def setup(bot):
    await bot.add_cog(FinanceCog(bot))
