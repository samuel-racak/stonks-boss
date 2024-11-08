import yfinance as yf
import pycountry


def is_valid_ticker(ticker, session):
    """Check if the ticker is valid by attempting to fetch data."""
    try:
        stock_data = yf.Ticker(ticker, session=session)
        info = stock_data.info

        return (
            info is not None and "symbol" in info and info["symbol"] == ticker.upper()
        )
    except Exception:
        return False


def get_country_flag(country_name):
    # Convert each letter to the corresponding regional indicator symbol
    country = pycountry.countries.get(name=country_name)
    if country:
        return "".join([chr(ord(letter) + 127397) for letter in country.alpha_2])

    return ""


exchange_suffixes = {
    "NYSE": "",  # No suffix needed for NYSE
    "NASDAQ": "",  # No suffix needed for NASDAQ
    "Euronext Paris": ".PA",  # Euronext Paris (for example: ORA.PA for Orange)
    "Börse Frankfurt": ".F",  # Frankfurt (example: DAI.F for Daimler)
    "London Stock Exchange": ".L",  # LSE (example: VOD.L for Vodafone)
    "BSE": ".BO",  # Bombay Stock Exchange (example: TATAMOTORS.BO for Tata Motors)
    "Tokyo Stock Exchange": ".T",  # Tokyo (example: 7203.T for Toyota)
    "Toronto Stock Exchange": ".TO",  # Toronto (example: RY.TO for Royal Bank of Canada)
    "Hong Kong Stock Exchange": ".HK",  # Hong Kong (example: 0005.HK for HSBC)
}


def get_full_ticker(ticker, exchange):
    """Get the full ticker symbol including the exchange suffix."""
    return f"{ticker}{exchange_suffixes.get(exchange, '')}"  # default to NYSE/ NASDAQ
