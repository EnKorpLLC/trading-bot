from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from pathlib import Path
from ..utils.payment_processor import PaymentProcessor
from ..utils.license_manager import LicenseManager
from typing import Optional
import datetime

app = FastAPI()
payment_processor = PaymentProcessor(os.getenv('STRIPE_SECRET_KEY'))
license_manager = LicenseManager()

class CouponRequest(BaseModel):
    code: str

class PaymentRequest(BaseModel):
    amount: int
    coupon: str = None

class PaymentComplete(BaseModel):
    payment_intent: str
    email: str

class CouponUpdate(BaseModel):
    discount_percent: Optional[int] = None
    max_uses: Optional[int] = None
    expiry_days: Optional[int] = None

@app.post("/api/validate-coupon")
async def validate_coupon(request: CouponRequest):
    discount = license_manager.validate_coupon(request.code)
    if discount is None:
        raise HTTPException(400, "Invalid coupon code")
    return {"valid": True, "discount": discount}

@app.post("/api/create-payment")
async def create_payment(request: PaymentRequest):
    result = payment_processor.create_payment_intent(
        request.amount,
        coupon_code=request.coupon
    )
    return result

@app.post("/api/complete-payment")
async def complete_payment(request: PaymentComplete):
    license_key = payment_processor.process_payment(
        request.payment_intent,
        request.email
    )
    if not license_key:
        raise HTTPException(400, "Payment processing failed")
        
    # Generate temporary download URL
    return {
        "downloadUrl": f"/download/{license_key}"
    }

@app.get("/download/{license_key}")
async def download(license_key: str):
    if not license_manager.validate_license(license_key):
        raise HTTPException(403, "Invalid license")
        
    file_path = Path("dist/TradingBot-Installer.exe")
    return FileResponse(
        file_path,
        filename="TradingBot-Installer.exe",
        media_type="application/octet-stream"
    )

@app.get("/api/coupons")
async def list_coupons(include_expired: bool = False):
    """List all coupons."""
    coupons = license_manager.list_coupons(include_expired)
    return {
        "coupons": [
            {
                "code": c.code,
                "discount_percent": c.discount_percent,
                "max_uses": c.max_uses,
                "uses_count": c.uses_count,
                "expiry_date": c.expiry_date.isoformat(),
                "created_at": c.created_at.isoformat(),
                "is_valid": (
                    c.expiry_date > datetime.datetime.utcnow() and 
                    c.uses_count < c.max_uses
                )
            }
            for c in coupons
        ]
    }

@app.get("/api/coupons/{code}")
async def get_coupon(code: str):
    """Get details of a specific coupon."""
    coupon = license_manager.get_coupon(code)
    if not coupon:
        raise HTTPException(404, "Coupon not found")
        
    return {
        "code": coupon.code,
        "discount_percent": coupon.discount_percent,
        "max_uses": coupon.max_uses,
        "uses_count": coupon.uses_count,
        "expiry_date": coupon.expiry_date.isoformat(),
        "created_at": coupon.created_at.isoformat(),
        "is_valid": (
            coupon.expiry_date > datetime.datetime.utcnow() and 
            coupon.uses_count < coupon.max_uses
        )
    }

@app.put("/api/coupons/{code}")
async def update_coupon(code: str, update: CouponUpdate):
    """Update coupon details."""
    expiry_date = None
    if update.expiry_days is not None:
        expiry_date = (datetime.datetime.utcnow() + 
                      datetime.timedelta(days=update.expiry_days))
        
    success = license_manager.update_coupon(
        code,
        discount_percent=update.discount_percent,
        max_uses=update.max_uses,
        expiry_date=expiry_date
    )
    
    if not success:
        raise HTTPException(400, "Failed to update coupon")
    return {"message": "Coupon updated successfully"}

@app.delete("/api/coupons/{code}")
async def delete_coupon(code: str):
    """Delete a coupon."""
    success = license_manager.delete_coupon(code)
    if not success:
        raise HTTPException(400, "Failed to delete coupon")
    return {"message": "Coupon deleted successfully"} 