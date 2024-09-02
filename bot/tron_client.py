from tronpy import Tron
from tronpy.providers import HTTPProvider
from bot.config import TRON_API_KEY

tron_client = Tron(provider=HTTPProvider(api_key=TRON_API_KEY))