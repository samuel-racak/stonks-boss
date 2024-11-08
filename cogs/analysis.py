from discord.ext import commands
from discord import app_commands, Embed, File
import yfinance as yf

# Libraries for creating graphs
import matplotlib.pyplot as plt
import io

plt.switch_backend("Agg")  # Change the backend to Agg to avoid displaying the graph

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
            last_bollinger_data, graph_data = self.get_bollinger_bands(ticker)
            image_stream = self.get_bollinger_bands_graph(ticker, graph_data)

            embed = Embed(
                title=f"Bollinger Bands for {ticker.upper()}",
                description="The Bollinger Bands are a volatility indicator that consists of a simple moving average and two standard deviations.",
                color=EMBED_COLOR_PRIMARY,
            )
            embed.set_image(url="attachment://bollinger.png")
            embed.add_field(
                name="Close Price (Current Price)",
                value=last_bollinger_data.get("Close", "N/A"),
                inline=False,
            )
            embed.add_field(
                name="Lower Band", value=last_bollinger_data.get("Lower Band", "N/A")
            )
            embed.add_field(
                name="Upper Band", value=last_bollinger_data.get("Upper Band", "N/A")
            )
            embed.set_footer(text=FOOTER_TEXT)

            await interaction.followup.send(
                embed=embed, file=File(image_stream, filename="bollinger.png")
            )
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    def get_bollinger_bands(self, ticker):
        """Calculate Bollinger Bands for the specified ticker."""
        # Fetch historical data
        stock_data = yf.download(
            ticker, period="3mo", interval="1d"
        )  # get data for the last 3 months so that we don't get null values for the rolling mean and standard deviation

        # trim the data to the last 40 days to get the most recent data for the graph while keeping all data for graphing purposes
        stock_data = stock_data[-40:]

        # Calculate the rolling mean and rolling standard deviation
        stock_data["MA"] = stock_data["Close"].rolling(window=20).mean()
        stock_data["STD"] = stock_data["Close"].rolling(window=20).std()

        # Calculate Bollinger Bands
        stock_data["Upper Band"] = stock_data["MA"] + (stock_data["STD"] * 2)
        stock_data["Lower Band"] = stock_data["MA"] - (stock_data["STD"] * 2)

        # Return the most recent values
        latest_data = stock_data[["Close", "Upper Band", "Lower Band"]].tail(1)

        # Flatten the DataFrame to a dictionary (assign column names)
        latest_data.columns = ["Close", "Upper Band", "Lower Band"]
        latest_data = latest_data.to_dict(orient="records")[0]

        # Round the values to two decimal places
        latest_data = {k: round(v, 2) for k, v in latest_data.items()}

        return (
            latest_data,
            stock_data[-20:],
        )  # Return the last 20 days of data (Medium term)

    def get_bollinger_bands_graph(self, ticker, stock_data):
        """Plot the Bollinger Bands for the specified ticker."""

        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(
            stock_data.index, stock_data["Close"], label="Close Price", color="blue"
        )
        ax.plot(
            stock_data.index,
            stock_data["Upper Band"],
            label="Upper Band",
            color="red",
            linestyle="--",
        )
        ax.plot(
            stock_data.index,
            stock_data["Lower Band"],
            label="Lower Band",
            color="red",
            linestyle="--",
        )
        ax.plot(
            stock_data.index,
            stock_data["MA"],
            label="Moving Average",
            color="green",
            linestyle="-.",
        )

        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.set_title(f"Bollinger Bands for {ticker.upper()}")
        ax.legend()

        # Save the plot to a BytesIO object
        image_stream = io.BytesIO()
        plt.savefig(image_stream, format="png")

        # Seek to the beginning of the stream for reading
        image_stream.seek(0)

        return image_stream


# Called when the cog is loaded
async def setup(bot):
    await bot.add_cog(AnalysisCog(bot, bot.session))
