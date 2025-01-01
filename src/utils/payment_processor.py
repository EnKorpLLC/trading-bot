from typing import Optional, Dict
import stripe
import logging
from pathlib import Path
from .license_manager import LicenseManager

logger = logging.getLogger(__name__)

class PaymentProcessor:
    def __init__(self, stripe_key: str):
        self.stripe = stripe
        self.stripe.api_key = stripe_key
        self.license_manager = LicenseManager()
        
    def create_payment_intent(self, amount: int, 
                            currency: str = 'usd',
                            coupon_code: Optional[str] = None) -> Dict:
        """Create a payment intent."""
        try:
            # Apply coupon if provided
            if coupon_code:
                discount = self.license_manager.validate_coupon(coupon_code)
                if discount:
                    amount = amount * (100 - discount) // 100
                    
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency
            )
            
            return {
                'client_secret': intent.client_secret,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise
            
    def process_payment(self, payment_intent_id: str,
                       user_email: str) -> Optional[str]:
        """Process a completed payment and generate license."""
        try:
            # Verify payment
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                # Generate license
                license_key = self.license_manager.generate_license(user_email)
                return license_key
                
            return None
            
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            return None 