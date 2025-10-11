from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TransactionType(str, Enum):
    BUY = "Покупка USDT"
    SELL = "Продажа USDT"


class ExchangeType(str, Enum):
    CHF_EUR = "Покупка CHF за EUR"
    EUR_CHF = "Покупка EUR за CHF"


class OperationType(str, Enum):
    INCOME = "Поступление"
    OUTCOME = "Списание"


class USDTExchangeRequest(BaseModel):
    client_fio: str = Field(default="")
    client_contact_info: str = Field(default="")
    transaction_type: TransactionType
    usdt_amount: str = Field(..., min_length=1)
    fiat_amount: str = Field(..., min_length=1)
    currency: str = Field(..., min_length=1)
    fiat_account: Optional[str] = None
    source: str = Field(default="Binance")
    from_bot: str = Field(default="Нет")
    manager: str = Field(default="")

    class Config:
        use_enum_values = True


class CurrencyExchangeRequest(BaseModel):
    client_fio: str = Field(default="")
    client_contact_info: str = Field(default="")
    exchange_type: ExchangeType
    chf_amount: str = Field(..., min_length=1)
    eur_amount: str = Field(..., min_length=1)
    from_account: str = Field(..., min_length=1)
    to_account: str = Field(..., min_length=1)
    manager: str = Field(default="")
    from_bot: str = Field(default="Нет")

    class Config:
        use_enum_values = True


class InternalTransferRequest(BaseModel):
    amount: str = Field(..., min_length=1)
    from_account: str = Field(..., min_length=1)
    to_account: str = Field(..., min_length=1)
    comment: str = Field(default="")


class OborotkaRequest(BaseModel):
    operation_type: OperationType
    amount: str = Field(..., min_length=1)
    currency: str = Field(..., min_length=1)
    account: str = Field(..., min_length=1)
    beneficiary: str = Field(..., min_length=1)
    comment: str = Field(default="")


class SuccessResponse(BaseModel):
    success: bool
    message: str
