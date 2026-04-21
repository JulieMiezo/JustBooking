from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models import ApplicationStatus, InvoicePlan, DocumentType


# ── Auth ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    display_name: str


# ── Step 1: 金流申請 ────────────────────────────────────────────
class Step1PaymentSchema(BaseModel):
    tax_id:               str = Field(..., min_length=8, max_length=8, pattern=r'^\d{8}$', description="8碼統編")
    brand_name_zh:        Optional[str] = Field(None, max_length=100)
    brand_name_en:        Optional[str] = Field(None, max_length=100)
    contact_email:        Optional[EmailStr] = None
    contact_phone:        Optional[str] = Field(None, max_length=20)
    payment_methods:      List[str] = Field(default_factory=list, description="['cc','apple','line','ipass','green']")
    payment_form_submitted: bool = False


# ── Step 3: 發票方案 ─────────────────────────────────────────────
class Step3InvoiceSchema(BaseModel):
    invoice_plan:    InvoicePlan
    contract_years:  int = Field(..., ge=1, le=3)
    invoice_year_fee: int
    setup_fee:       int


# ── Step 4: 加值服務 ─────────────────────────────────────────────
class Step4AddonSchema(BaseModel):
    addon_print_invoice: bool = False
    addon_pdf_send:      bool = False
    addon_multi_channel: bool = False


# ── Step 5: 確認送出 ─────────────────────────────────────────────
class Step5SubmitSchema(BaseModel):
    confirmed: bool = True


# ── Query（客戶查詢進度）────────────────────────────────────────
class DocumentOut(BaseModel):
    doc_type:      DocumentType
    original_name: Optional[str]
    uploaded_at:   datetime

    class Config:
        from_attributes = True

class ApplicationQueryOut(BaseModel):
    tax_id:           str
    brand_name_zh:    Optional[str]
    brand_name_en:    Optional[str]
    contact_email:    Optional[str]
    payment_methods:  List[str]
    invoice_plan:     Optional[str]
    contract_years:   int
    invoice_year_fee: int
    setup_fee:        int
    addon_print_invoice: bool
    addon_pdf_send:   bool
    addon_multi_channel: bool
    status:           ApplicationStatus
    current_step:     int
    submitted_at:     Optional[datetime]
    updated_at:       Optional[datetime]
    documents:        List[DocumentOut] = []

    class Config:
        from_attributes = True


# ── Admin: 客戶列表 ──────────────────────────────────────────────
class ApplicationListItem(BaseModel):
    id:              int
    tax_id:          str
    brand_name_zh:   Optional[str]
    brand_name_en:   Optional[str]
    contact_email:   Optional[str]
    payment_methods: List[str]
    invoice_plan:    Optional[str]
    contract_years:  int
    status:          ApplicationStatus
    current_step:    int
    created_at:      datetime
    updated_at:      Optional[datetime]
    submitted_at:    Optional[datetime]

    class Config:
        from_attributes = True

class ApplicationDetail(ApplicationListItem):
    contact_phone:      Optional[str]
    invoice_year_fee:   int
    setup_fee:          int
    addon_print_invoice: bool
    addon_pdf_send:     bool
    addon_multi_channel: bool
    admin_note:         Optional[str]
    documents:          List[DocumentOut] = []

    class Config:
        from_attributes = True


# ── Admin: 狀態更新 ──────────────────────────────────────────────
class StatusUpdateSchema(BaseModel):
    status:     ApplicationStatus
    admin_note: Optional[str] = None


# ── Common Response ──────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
    success: bool = True
