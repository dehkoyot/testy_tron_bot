import aiohttp
from tronpy.keys import PrivateKey
from cryptography.fernet import Fernet
from bot.tron_client import tron_client
from bot.config import ENCRYPTION_KEY
from loguru import logger

cipher = Fernet(ENCRYPTION_KEY)


def create_wallet(user_id: int) -> tuple[str, str]:
    try:
        priv_key = PrivateKey.random()
        print(priv_key)
        address = priv_key.public_key.to_base58check_address()
        encrypted_private_key = cipher.encrypt(
            priv_key.hex().encode()).decode()
        logger.info(f"User {user_id} created wallet with address {address}")
        return address, encrypted_private_key

    except Exception as e:
        logger.exception(f"Failed to create wallet: {e}")
        raise


def get_decrypted_private_key(encrypted_private_key: str) -> str:
    try:
        return cipher.decrypt(encrypted_private_key.encode()).decode()

    except Exception as e:
        logger.exception(f"Failed to decrypt private key: {e}")
        raise


async def get_wallet_balance(user: dict) -> tuple:
    address = user['address']
    trx_balance = tron_client.get_account_balance(address)
    async with aiohttp.ClientSession() as session:
        trc20_tokens = await get_trc20_balances_async(session, address)
    return trx_balance, trc20_tokens


async def get_trc20_balances_async(session, address):
    url = f"https://apilist.tronscan.org/api/account/tokens?address={address}"
    async with session.get(url) as response:
        if response.status == 200:
            tokens_data = await response.json()
            tokens = tokens_data.get('data', [])
            return {
                token['tokenName']: {
                    'amount': int(token['balance']) / 10**int(token['tokenDecimal']),
                    'contract_address': token['tokenId']
                }
                for token in tokens
                if token.get('tokenType') == 'trc20'
            }
        else:
            return None
