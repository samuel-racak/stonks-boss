from discord.ext import commands
from discord import app_commands
import yfinance as yf  # To fetch financial data


class FinanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            await interaction.followup.send(
                f"Current price for {ticker}: {round(current_price, 2)} USD"
            )
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(
        name="basic_info",
        description="Get basic information for a given ticker symbol.",
    )
    async def basic_info(self, interaction, ticker: str):
        """Fetch basic information for the specified ticker."""
        await interaction.response.defer()
        if not self.is_valid_ticker(ticker):
            await interaction.followup.send(
                f"The ticker '{ticker}' is not valid. Please check and try again."
            )
            return

        try:
            info = self.get_basic_info(ticker)
            name = info["longName"]
            sector = info["sector"]
            country = info["country"]
            market_cap = info["marketCap"]
            currency = info["currency"]
            await interaction.followup.send(
                f"Basic information for {ticker}:\n"
                f"Name: {name}\n"
                f"Sector: {sector}\n"
                f"Country: {country}\n"
                f"Market Cap: {market_cap} {currency}"
            )
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

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

    def is_valid_ticker(self, ticker):
        """Check if the ticker is valid by attempting to fetch data."""
        try:
            stock_data = yf.Ticker(ticker)
            print(stock_data)

            # If we can fetch info, the ticker is valid
            info = stock_data.info
            return (
                info is not None
                and "symbol" in info
                and info["symbol"] == ticker.upper()
                # and stock_data.history(period="1d")
                is not None  # Check if the price is available (might have been delisted)
            )
        except Exception as e:
            return False

    def get_current_price(self, ticker):
        # Fetch the current stock price using yfinance
        stock_data = yf.Ticker(ticker)
        history = stock_data.history(period="1d")
        if history.empty:
            raise ValueError(f"No data found for ticker '{ticker}'")
        price = history["Close"].iloc[-1]
        return price

    def get_basic_info(self, ticker):
        """Fetch basic information for the specified ticker."""
        stock_data = yf.Ticker(ticker)
        info = stock_data.info
        return info

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


async def setup(bot):
    await bot.add_cog(FinanceCog(bot))
