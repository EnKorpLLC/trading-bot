from coinbase.rest import RESTClient
import logging
from typing import Optional, Dict, List
import time

logger = logging.getLogger(__name__)

class TradingAPIClient:
    def __init__(self, api_key: str, api_secret: str):
        self.client = RESTClient(api_key=api_key, api_secret=api_secret)
        logger.info("API client initialized")

    def get_accounts(self) -> List[Dict]:
        """Get all trading accounts."""
        try:
            accounts = self.client.get_accounts()
            return [
                {
                    'name': account.name,
                    'balance': account.available_balance.value,
                    'currency': account.available_balance.currency
                }
                for account in accounts.accounts
            ]
        except Exception as e:
            logger.error(f"Error fetching accounts: {str(e)}")
            raise

    def get_products(self) -> List[Dict]:
        """Get available trading products."""
        try:
            products = self.client.get_products()
            return [
                {
                    'id': product.product_id,
                    'base_currency': product.base_currency,
                    'quote_currency': product.quote_currency,
                    'price': product.price
                }
                for product in products
            ]
        except Exception as e:
            logger.error(f"Error fetching products: {str(e)}")
            raise

    def place_market_order(self, 
                          product_id: str, 
                          side: str, 
                          size: float) -> Dict:
        """Place a market order."""
        try:
            order = self.client.create_market_order(
                product_id=product_id,
                side=side,
                size=str(size)
            )
            return {
                'id': order.order_id,
                'status': order.status,
                'size': order.size,
                'product_id': order.product_id
            }
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            raise 