from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from pathlib import Path
from ..utils.payment_processor import PaymentProcessor
from ..utils.license_manager import LicenseManager

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