import time
from tronpy import Contract
from bot.config import AMOUNT_TRX_TO_SPEND, MAX_SLIPPAGE, SUNPUMP_ROUTER_ADDRESS, TOKEN_SELL_PERCENTAGE, TRC20_ABI, UNLIMITED_AMOUNT_TO_SPEND, WTRX_CONTRACT_ADDRESS
from bot.tron_client import tron_client
from tronpy.keys import PrivateKey
from loguru import logger


def buy_token(token_address: str, user_address: str, private_key_hex: str) -> bool:
    try:
        priv_key = PrivateKey(bytes.fromhex(private_key_hex))

        contract = tron_client.get_contract(SUNPUMP_ROUTER_ADDRESS)

        deadline = int(time.time()) + 300

        path = get_token_pair(WTRX_CONTRACT_ADDRESS, token_address)

        amounts_out = contract.functions.getAmountsOut(
            AMOUNT_TRX_TO_SPEND, path)
        slippage_tolerance = MAX_SLIPPAGE
        amount_out_min = int(amounts_out[-1] * (1 - slippage_tolerance))

        txn = (
            contract.functions.swapExactETHForTokens.with_transfer(AMOUNT_TRX_TO_SPEND)(
                amountOutMin=amount_out_min,
                path=path,
                to=user_address,
                deadline=deadline
            )
            .with_owner(user_address)
            .fee_limit(5_000_000)
            .build()
            .sign(priv_key)
            .broadcast()
        )

        return handle_transaction(txn)

    except Exception as e:
        logger.error(f"Error performing trade: {e}")
        return False


def sell_token(token_address: str, user_address: str, private_key_hex: str) -> bool:
    try:
        token_contract = tron_client.get_contract(token_address)
        token_contract.abi = TRC20_ABI

        priv_key = PrivateKey(bytes.fromhex(private_key_hex))

        if not is_approved(token_contract, user_address):
            approve(token_contract, user_address, priv_key)

        deadline = int(time.time()) + 300
        path = get_token_pair(token_address, WTRX_CONTRACT_ADDRESS)

        token_balance = token_contract.functions.balanceOf(user_address)
        amount_in = int(token_balance * TOKEN_SELL_PERCENTAGE)

        router_contract = tron_client.get_contract(SUNPUMP_ROUTER_ADDRESS)

        amounts_out = router_contract.functions.getAmountsOut(amount_in, path)
        amount_out_min = int(amounts_out[1] * (1 - MAX_SLIPPAGE))

        txn = (
            router_contract.functions.swapExactTokensForETH(
                amountIn=amount_in,
                amountOutMin=amount_out_min,
                path=path,
                to=user_address,
                deadline=deadline
            )
            .with_owner(user_address)
            .fee_limit(5_000_000)
            .build()
            .sign(priv_key)
            .broadcast()
        )

        return handle_transaction(txn)

    except Exception as e:
        logger.error(f"Error performing trade: {e}")
        return False


def is_approved(token_contract: Contract, user_address: str) -> bool:
    try:
        amount_approved = token_contract.functions.allowance(
            user_address, SUNPUMP_ROUTER_ADDRESS)
        return amount_approved > 0

    except Exception as e:
        logger.error(f"Error performing approve check: {e}")
        return False


def approve(token_contract: Contract, user_address: str, priv_key: str) -> bool:
    try:
        txn = (
            token_contract.functions.approve(
                SUNPUMP_ROUTER_ADDRESS,
                UNLIMITED_AMOUNT_TO_SPEND
            )
            .with_owner(user_address)
            .fee_limit(15_000_000)
            .build()
            .sign(priv_key)
            .broadcast()
        )

        return handle_transaction(txn)

    except Exception as e:
        logger.error(f"Error performing approve: {e}")
        return False


def get_token_pair(from_token_address: str, to_token_address: str) -> list:
    token_in = tron_client.to_hex_address(from_token_address)
    token_out = tron_client.to_hex_address(to_token_address)
    return [token_in, token_out]


def handle_transaction(txn):
    txn_receipt = txn.wait()
    result = txn_receipt.get('receipt', {}).get('result')

    if result == 'SUCCESS':
        logger.success(f"Transaction successful: {txn['txid']}")
        return True
    else:
        error_message = txn_receipt.get('resMessage')
        logger.error(f"Transaction failed: {error_message}, txnId: {txn['txid']}")
        return False