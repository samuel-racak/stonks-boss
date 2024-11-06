import yfinance as yf
import pycountry


def is_valid_ticker(ticker, session):
    """Check if the ticker is valid by attempting to fetch data."""
    try:
        stock_data = yf.Ticker(ticker, session=session)
        info = stock_data.info

        print(f"Ticker type IS_VALID: {type(ticker)}")  # Should be <class 'str'>

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
