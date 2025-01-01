# paypal_utils.py
import paypalrestsdk
from django.conf import settings

def configure_paypal():
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_ENVIRONMENT,
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET,
    })

def create_paypal_order(amount, currency="USD"):
    configure_paypal()
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": "http://localhost:3000/payment-success",
            "cancel_url": "http://localhost:3000/payment-cancel",
        },
        "transactions": [{
            "amount": {
                "total": f"{amount:.2f}",
                "currency": currency,
            },
            "description": "Payment description",
        }]
    })

    if payment.create():
        return payment
    else:
        raise Exception(payment.error)
