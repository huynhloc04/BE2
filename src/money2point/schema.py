from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from fastapi import File, Form, UploadFile
from pydantic import BaseModel


class Currency(str, Enum):
    vnd = "vnd"
    usd = "usd"

    def __str__(self):
        return f"{self.value}"


class TransactionForm(str, Enum):
    banking = "banking"
    e_wallet = "e_wallet"
    credit_card = "credit_card"

    def __str__(self):
        return f"{self.value}"


class CustomResponse(BaseModel):
    message: str = None
    data: Any = None
    
class PointPackage(BaseModel):
    point: int
    price: float
    currency: Currency

class PurchasePoint(BaseModel):
    package_id: int
    quantity: int
    total_price: float
    transaction_form: TransactionForm
