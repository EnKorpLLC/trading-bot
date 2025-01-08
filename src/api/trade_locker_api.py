"""
TradeLocker API Client
Version: 2.11.0
"""

import requests
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeLockerAPI:
    """TradeLocker REST API Client"""
    
    DEMO_URL = "demo.tradelocker.com/backend-api/"
    LIVE_URL = "live.tradelocker.com/backend-api/"
    
    def __init__(self, is_demo: bool = True):
        """
        Initialize TradeLocker API client
        
        Args:
            is_demo (bool): Use demo environment if True, live if False
        """
        self.base_url = self.DEMO_URL if is_demo else self.LIVE_URL
        self.access_token = None
        self.refresh_token = None
        self.acc_num = None
        self.account_id = None
        self.route_id = None
    
    def authenticate(self, email: str, password: str, server: str) -> bool:
        """
        Authenticate with TradeLocker and get JWT tokens
        
        Args:
            email (str): User email
            password (str): User password
            server (str): Server name
            
        Returns:
            bool: True if authentication successful
        """
        try:
            response = requests.post(
                f"{self.base_url}/auth/jwt/token",
                json={
                    "email": email,
                    "password": password,
                    "server": server
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["accessToken"]
                self.refresh_token = data["refreshToken"]
                
                # Get account details
                accounts = self.get_all_accounts()
                if accounts:
                    self.acc_num = accounts[0]["accNum"]  # Use first account
                    self.account_id = accounts[0]["accountId"]
                
                return True
            else:
                logger.error(f"Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def refresh_auth_token(self) -> bool:
        """Refresh the JWT token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/jwt/refresh",
                headers=self._get_headers(),
                json={"refreshToken": self.refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["accessToken"]
                return True
            return False
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all user accounts"""
        return self._make_request("GET", "/auth/jwt/all-accounts")
    
    def get_account_details(self) -> Dict:
        """Get details for the current account"""
        return self._make_request("GET", "/trade/accounts")
    
    def get_config(self) -> Dict:
        """Get API configuration including rate limits"""
        return self._make_request("GET", "/trade/config")
    
    def place_order(self, 
                   qty: float,
                   side: str,
                   order_type: str = "market",
                   validity: str = "GTC",
                   price: Optional[float] = None,
                   stop_loss: Optional[float] = None,
                   take_profit: Optional[float] = None,
                   instrument_id: Optional[str] = None) -> Dict:
        """
        Place a new trading order
        
        Args:
            qty (float): Order quantity
            side (str): "buy" or "sell"
            order_type (str): "market", "limit", or "stop"
            validity (str): "GTC" or "IOC"
            price (float, optional): Limit price for limit orders
            stop_loss (float, optional): Stop loss price
            take_profit (float, optional): Take profit price
            instrument_id (str, optional): Tradable instrument ID
        """
        data = {
            "qty": qty,
            "routeId": self.route_id,
            "side": side,
            "validity": validity,
            "type": order_type,
            "tradableInstrumentId": instrument_id
        }
        
        if price:
            data["price"] = price
        if stop_loss:
            data["stopLoss"] = stop_loss
        if take_profit:
            data["takeProfit"] = take_profit
            
        return self._make_request(
            "POST",
            f"/trade/accounts/{self.account_id}/orders",
            json=data
        )
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        response = self._make_request(
            "DELETE",
            f"/trade/accounts/{self.account_id}/orders/{order_id}"
        )
        return response.get("success", False)
    
    def modify_order(self, 
                    order_id: str,
                    qty: Optional[float] = None,
                    price: Optional[float] = None,
                    stop_loss: Optional[float] = None,
                    take_profit: Optional[float] = None) -> Dict:
        """Modify an existing order"""
        data = {}
        if qty:
            data["qty"] = qty
        if price:
            data["price"] = price
        if stop_loss:
            data["stopLoss"] = stop_loss
        if take_profit:
            data["takeProfit"] = take_profit
            
        return self._make_request(
            "PATCH",
            f"/trade/orders/{order_id}",
            json=data
        )
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        return self._make_request(
            "GET",
            f"/trade/accounts/{self.account_id}/positions"
        )
    
    def close_position(self, position_id: str) -> bool:
        """Close an open position"""
        response = self._make_request(
            "DELETE",
            f"/trade/accounts/{self.account_id}/positions/{position_id}"
        )
        return response.get("success", False)
    
    def modify_position(self,
                       position_id: str,
                       stop_loss: Optional[float] = None,
                       take_profit: Optional[float] = None) -> Dict:
        """Modify an existing position"""
        data = {}
        if stop_loss:
            data["stopLoss"] = stop_loss
        if take_profit:
            data["takeProfit"] = take_profit
            
        return self._make_request(
            "PATCH",
            f"/trade/positions/{position_id}",
            json=data
        )
    
    def get_instruments(self) -> List[Dict]:
        """Get list of available trading instruments"""
        return self._make_request(
            "GET",
            f"/trade/accounts/{self.account_id}/instruments"
        )
    
    def get_instrument_details(self, instrument_id: str) -> Dict:
        """Get details for a specific instrument"""
        return self._make_request(
            "GET",
            f"/trade/instruments/{instrument_id}"
        )
    
    def get_quotes(self, instrument_ids: List[str]) -> Dict:
        """Get current quotes for instruments"""
        return self._make_request(
            "GET",
            "/trade/quotes",
            params={"instrumentIds": ",".join(instrument_ids)}
        )
    
    def get_market_depth(self, instrument_id: str) -> Dict:
        """Get market depth for an instrument"""
        return self._make_request(
            "GET",
            "/trade/depth",
            params={"instrumentId": instrument_id}
        )
    
    def get_history(self,
                   instrument_id: str,
                   start_time: datetime,
                   end_time: datetime,
                   interval: str = "1m") -> List[Dict]:
        """
        Get historical price data
        
        Args:
            instrument_id (str): Instrument ID
            start_time (datetime): Start time
            end_time (datetime): End time
            interval (str): Time interval (e.g., "1m", "5m", "1h", "1d")
        """
        return self._make_request(
            "GET",
            "/trade/history",
            params={
                "instrumentId": instrument_id,
                "from": int(start_time.timestamp() * 1000),
                "to": int(end_time.timestamp() * 1000),
                "interval": interval
            }
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        if self.acc_num:
            headers["accNum"] = self.acc_num
        return headers
    
    def _make_request(self,
                     method: str,
                     endpoint: str,
                     params: Optional[Dict] = None,
                     json: Optional[Dict] = None) -> Union[Dict, List, None]:
        """
        Make an API request with error handling and token refresh
        
        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            json (dict, optional): JSON body data
        """
        try:
            url = f"{self.base_url.rstrip('/')}{endpoint}"
            response = requests.request(
                method,
                url,
                headers=self._get_headers(),
                params=params,
                json=json
            )
            
            # Handle token expiration
            if response.status_code == 401:
                if self.refresh_auth_token():
                    # Retry request with new token
                    response = requests.request(
                        method,
                        url,
                        headers=self._get_headers(),
                        params=params,
                        json=json
                    )
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                logger.error(f"API request failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None 