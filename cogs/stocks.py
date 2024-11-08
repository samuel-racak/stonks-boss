from discord.ext import commands
from discord import app_commands, Embed, File

# Libraries for creating graphs
import io
import os
import tempfile

# Libaries for fetching data
import yfinance as yf

# Libararies for multi-threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Graphs
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

plt.switch_backend(
    "Agg"
)  # Change the backend to Agg to avoid displaying the graph (use on backend)

# Import utils
from cogs.utils import (
    is_valid_ticker,
    get_country_flag,
    get_full_ticker,
    exchange_suffixes,
)

# Import constants
from constants import EMBED_COLOR_PRIMARY, FOOTER_TEXT


class StocksCog(commands.Cog):
    """
    A cog for fetching stock data using the Yahoo Finance API.
    This cog provides basic commands aimed at absolute basics such as current_price, name, sector, country, market cap, and currency.
    """

    def __init__(self, bot, session):
        self.bot = bot
        # Use a single session across the class to cache and limit requests
        # (session is created in main.py and added through the bot instance)
        # TODO: Think about this
        self.session = session
        self.executor = (
            ThreadPoolExecutor()
        )  # Create a ThreadPoolExecutor for multi-threading

    async def run_in_executor(self, func, *args, **kwargs):
        """Run a function in a separate thread using the ThreadPoolExecutor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)

    @app_commands.command(
        name="price",
        description="Get price for a given ticker symbol.",
    )
    @app_commands.describe(
        ticker="The ticker symbol of the stock",
        period="Time period for the data (e.g., '1mo', '3mo')",
        exchange="The stock exchange where the ticker is listed",
    )
    @app_commands.choices(
        period=[
            app_commands.Choice(name="1 month", value="1mo"),
            app_commands.Choice(name="3 months", value="3mo"),
            app_commands.Choice(name="6 months", value="6mo"),
            app_commands.Choice(name="1 year", value="1y"),
        ]
    )
    @app_commands.choices(
        exchange=[
            app_commands.Choice(name=exchange, value=exchange)
            for exchange in exchange_suffixes.keys()
        ]
    )
    async def price(
        self, interaction, ticker: str, period: str = "1mo", exchange: str = "NYSE"
    ):
        """Fetch current price for the specified ticker."""
        await interaction.response.defer()
        ticker = get_full_ticker(ticker, exchange)

        if not is_valid_ticker(ticker, session=self.session):
            await interaction.followup.send(
                f"The ticker '{ticker}' does not exist. Please check and try again."
            )
            return

        try:
            image_stream = await self.run_in_executor(
                self.get_price_graph, ticker, period
            )

            embed = Embed(
                title=f"{ticker.upper()} Price Overview",
                description=f"Price data for the last {period}",
                color=EMBED_COLOR_PRIMARY,
            )
            embed.set_image(
                url="attachment://price_animation.gif"
            )  # Link to the image to attach

            # additional fields
            ticker_info = yf.Ticker(ticker, session=self.session)
            current_price = self.get_current_price(ticker)
            market_cap = ticker_info.info["marketCap"]

            embed.add_field(
                name="Current Price",
                value=f"{current_price} USD",
                inline=True,
            )
            embed.add_field(name="Market Cap", value=f"{market_cap} USD", inline=True)
            embed.set_footer(text=FOOTER_TEXT)

            await interaction.followup.send(
                embed=embed,
                file=File(image_stream, filename="price_animation.gif"),
            )

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    @app_commands.command(
        name="basic_info",
        description="Get basic information for a given ticker symbol.",
    )
    @app_commands.choices(
        exchange=[
            app_commands.Choice(name=exchange, value=exchange)
            for exchange in exchange_suffixes.keys()
        ]
    )
    async def basic_info(self, interaction, ticker: str, exchange: str = "NYSE"):
        """Fetch name, sector, country, market_cap and currency for the specified ticker."""
        await interaction.response.defer()
        ticker = get_full_ticker(ticker, exchange)
        if not is_valid_ticker(ticker, session=self.session):
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

            # Get the flag for the country code if it exists
            country_code = info.get("country")  # Adjust this field if it's different
            country_flag = get_country_flag(country_code)
            country_display = f"{country_flag} {country}" if country_flag else country

            # Create an embed to display the basic information
            embed = Embed(
                title=f"Basic Information for {ticker.upper()}",
                color=EMBED_COLOR_PRIMARY,
            )
            embed.add_field(name="Name", value=name, inline=False)
            embed.add_field(name="Sector", value=sector, inline=True)
            embed.add_field(name="Country", value=country_display, inline=True)
            embed.add_field(
                name="Market Cap", value=f"{market_cap:,} {currency}", inline=False
            )
            embed.set_footer(text=FOOTER_TEXT)

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}")

    def get_current_price(self, ticker):
        """Fetch the current stock price using yfinance."""
        stock_data = yf.Ticker(ticker, session=self.session)
        history = stock_data.history(period="1d")
        if history.empty:
            raise ValueError(f"No data found for ticker '{ticker}'")
        price = history["Close"].iloc[-1]
        return round(price, 2)

    def get_price_graph(self, ticker, period="1mo"):
        data = yf.Ticker(ticker, session=self.session).history(period=period)

        # Initialize the figure and axis
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title(f"{ticker.upper()} Price ({period})")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        ax.set_xlim(data.index[0], data.index[-1])
        ax.set_ylim(data["Close"].min() - 5, data["Close"].max() + 5)

        # Initialize line and color data
        (line,) = ax.plot([], [], label="Close Price", color="blue")
        ax.legend()

        def update(frame):
            # Get the data up to the current frame
            x_data = data.index[:frame]
            y_data = data["Close"][:frame]

            # Check the overall price change for the entire period at the start
            if frame == 1:
                # Calculate the price change for the whole period (from start to end)
                price_change = data["Close"].iloc[-1] - data["Close"].iloc[0]

                # If price increased, set the color to green, else red
                if price_change > 0:
                    line.set_color("green")  # Green for overall price increase
                else:
                    line.set_color("red")  # Red for overall price decrease

            # Update the data for the line
            line.set_data(x_data, y_data)
            return (line,)

        # Create the animation
        anim = FuncAnimation(fig, update, frames=len(data), interval=100, repeat=False)

        # Save the animation to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_file:
            temp_path = temp_file.name
            writer = PillowWriter(fps=60)
            anim.save(temp_path, writer=writer, dpi=80)  # Save the animation as GIF

        # Save the animation to a BytesIO object
        image_stream = io.BytesIO()
        with open(temp_path, "rb") as temp_file:
            image_stream.write(temp_file.read())

        os.remove(temp_path)

        # Seek to the beginning of the BytesIO stream for reading
        image_stream.seek(0)

        return image_stream

    def get_basic_info(self, ticker):
        """Fetch basic information for the specified ticker."""
        stock_data = yf.Ticker(ticker, session=self.session)
        info = stock_data.info
        return info


# Called when the cog is loaded
async def setup(bot):
    await bot.add_cog(StocksCog(bot, bot.session))
