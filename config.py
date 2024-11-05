from pydantic_settings import BaseSettings
from pydantic import ValidationError
from dotenv import load_dotenv

# Load env variables
load_dotenv()


class BotConfig(BaseSettings):
    DISCORD_TOKEN: str = "DISCORD_TOKEN"
    DEBUG_MODE: bool = "DEBUG_MODE"
    COMMAND_PREFIX: str = "COMMAND_PREFIX"


# Attempt to create the config
try:
    config = BotConfig()
    print("Configuration loaded successfully!")
except ValidationError as e:
    print("Configuration error:", e)
    exit(1)

# Access validated config values
print(config.DISCORD_TOKEN)
print(config.COMMAND_PREFIX)
print(config.DEBUG_MODE)
