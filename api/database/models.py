from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

@dataclass
class UserSession:
    session_id: str
    created_at: datetime
    expires_at: datetime

@dataclass
class Document:
    id: Optional[int]
    session_id: str
    file_name: str
    file_url: Optional[str]
    file_type: str
    upload_timestamp: datetime

@dataclass
class UserInput:
    id: Optional[int]
    session_id: str
    input_type: str
    field_name: str
    field_value: Optional[str]
    timestamp: datetime

@dataclass
class TaxCalculation:
    id: Optional[int]
    session_id: str
    gross_income: Optional[Decimal]
    tax_old_regime: Optional[Decimal]
    tax_new_regime: Optional[Decimal]
    total_deductions: Optional[Decimal]
    net_tax: Optional[Decimal]
    calculation_timestamp: datetime

@dataclass
class AIConversation:
    id: Optional[int]
    session_id: str
    user_message: str
    ai_response: str
    timestamp: datetime 