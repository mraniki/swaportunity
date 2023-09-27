"""
 DEX SWAP
🔒 USER RELATED
"""


from loguru import logger

from dxsp.config import settings


class AccountUtils:

    """
    Class AccountUtils to interact with private related methods
    such as account balance, signing transactions, etc.

    Args:
        None

    Methods:
        get_info()
        get_help()
        get_account_balance()
        get_trading_asset_balance()
        get_account_position
        get_account_margin
        get_account_open_positions
        get_account_transactions()
        get_account_pnl
        get_approve
        get_sign
        get_gas
        get_gas_price

    """

    def __init__(
        self,
        w3,
        contract_utils,
        wallet_address,
        private_key,
        trading_asset_address,
        block_explorer_url,
        block_explorer_api,
    ):
        self.w3 = w3
        self.wallet_address = self.w3.to_checksum_address(wallet_address)
        self.account_number = (
            f"{str(self.w3.net.version)} - " f"{str(self.wallet_address)[-8:]}"
        )
        logger.debug(f"account number: {self.account_number}")
        self.private_key = private_key
        self.trading_asset_address = self.w3.to_checksum_address(trading_asset_address)
        self.contract_utils = contract_utils
        self.block_explorer_url = block_explorer_url
        self.block_explorer_api = block_explorer_api

    async def get_account_balance(self):
        """
        Retrieves the account balance of the user.

        Returns:
            str: A formatted string containing
            the account balance in Bitcoin (₿) and
            the trading asset balance like USDT (💵).
        """
        account_balance = self.w3.eth.get_balance(
            self.w3.to_checksum_address(self.wallet_address)
        )
        account_balance = self.w3.from_wei(account_balance, "ether") or 0
        trading_asset_balance = await self.get_trading_asset_balance()
        balance = f"🏦 Balance {self.account_number} \n"
        balance += f"₿ {round(account_balance,5)}\n💵 {trading_asset_balance}"
        return balance

    async def get_trading_asset_balance(self):
        """
        Retrieves the balance of the trading asset
        for the current wallet address.

        Returns:
            The balance of the trading asset as a float.
            If the balance is not available,
            it returns 0.
        """
        trading_asset_balance = await self.contract_utils.get_token_balance(
            self.trading_asset_address, self.wallet_address
        )
        return trading_asset_balance if trading_asset_balance else 0

    async def get_account_position(self):
        """
        Retrieves the account position.

        Returns:
            str: A string representing the account position.
        """
        position = f"📊 Position {self.account_number} \n"
        position += f"Opened: {str(await self.get_account_open_positions())}\n"
        position += f"Margin: {str(await self.get_account_margin())}"
        return position

    async def get_account_margin(self):
        """
        Get the account margin. Not yet implemented

        Returns:
            int: The account margin.
        """
        return 0

    async def get_account_open_positions(self):
        """
        Get the open positions for the account.
        Not yet implemented

        :return: The number of open positions
        for the account.
        """
        return 0

    # async def get_account_transactions(
    #     self,
    #     contract_address,
    #     period=24,
    # ):
    #     """
    #     Retrieves the account transactions
    #     within a specified time period
    #     for the main asset activity
    #     Not yet implemented

    #     :param contract_address: The address of the contract.
    #     :type contract_address: str
    #     :param wallet_address: The address of the wallet.
    #     :type wallet_address: str
    #     :param period: The time period in hours
    #     :type period: int

    #     :return: The transactions for the account.
    #     """
    #     pnl_dict = {"pnl": 0, "tokenList": {}}
    #     if not self.block_explorer_api:
    #         return pnl_dict

    #     params = {
    #         "module": "account",
    #         "action": "tokentx",
    #         "contractaddress": contract_address,
    #         "address": self.wallet_address,
    #         "page": "1",
    #         "offset": "100",
    #         "startblock": "0",
    #         "endblock": "99999999",
    #         "sort": "desc",
    #         "apikey": self.block_explorer_api,
    #     }

    #     response = await get(url=self.block_explorer_url, params=params)

    #     if response.get("status") == "1" and "result" in response:
    #         current_time = datetime.utcnow()
    #         time_history_start = current_time - timedelta(hours=period)

    #         for entry in response["result"]:
    #             token_symbol = entry.get("tokenSymbol")
    #             value = int(entry.get("value", 0))
    #             timestamp = int(entry.get("timeStamp", 0))
    #             transaction_time = datetime.utcfromtimestamp(timestamp)

    #             if transaction_time >= time_history_start and token_symbol:
    #                 pnl_dict["tokenList"][token_symbol] = (
    #                     pnl_dict["tokenList"].get(token_symbol, 0) + value
    #                 )
    #                 pnl_dict["pnl"] += value

    #     return pnl_dict

    # async def get_account_pnl(self, period=24):
    #     """
    #     Create a profit and loss (PnL)
    #     report for the account.
    #     Not yet implemented

    #     Args:
    #         period (int): The time period in hours
    #         to retrieve the PnL for. Default is 24 hours.

    #     Returns:
    #         str: A string containing the PnL report.

    #     """
    #     pnl_dict = await self.get_account_transactions(period)
    #     pnl_report = "".join(
    #         f"{token} {value}\n" for token, value in pnl_dict["tokenList"].items()
    #     )
    #     pnl_report += f"{self.name}: {pnl_dict['pnl']}\n"
    #     pnl_report += await self.get_account_position()

    #     return pnl_report

    async def get_approve(self, token_address):
        """
        Given a token address, approve a token

        Args:
            token_address (str): The token address

        Returns:
            approval_tx_hash

        """
        try:
            contract = await self.contract_utils.get_token_contract(token_address)
            if contract is None:
                return
            approved_amount = self.w3.to_wei(2**64 - 1, "ether")
            owner_address = self.w3.to_checksum_address(self.wallet_address)
            dex_router_address = self.w3.to_checksum_address(
                settings.dex_router_contract_addr
            )
            allowance = contract.functions.allowance(
                owner_address, dex_router_address
            ).call()
            if allowance == 0:
                approval_tx = contract.functions.approve(
                    dex_router_address, approved_amount
                )
                approval_tx_hash = await self.get_sign(approval_tx.transact())
                return self.w3.eth.wait_for_transaction_receipt(approval_tx_hash)
        except Exception as error:
            logger.error("Approval failed {}", error)

    async def get_sign(self, transaction):
        """
        Given a transaction, sign a transaction

        Args:
            transaction (Transaction): The transaction

        Returns:
            signed_tx_hash

        """
        try:
            signed_tx = self.w3.eth.account.sign_transaction(
                transaction, self.private_key
            )
            return self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        except Exception as error:
            logger.error("Sign failed {}", error)

    async def get_gas(self, transaction):
        """
        Given a transaction, get gas estimate

        Args:
            transaction (Transaction): The transaction

        Returns:
            int: The gas estimate

        """
        gas_limit = self.w3.eth.estimate_gas(transaction) * 1.25
        return int(self.w3.to_wei(gas_limit, "wei"))

    async def get_gas_price(self):
        """
        search get gas price

        Returns:
            int: The gas price

        """
        return round(self.w3.from_wei(self.w3.eth.generate_gas_price(), "gwei"), 2)
