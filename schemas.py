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
    tax_id:               str = Field(..., min_length=8, max_length=20, description="統一編號或身分證字號")
    applicant_type:       Optional[str] = Field(None, max_length=10, description="company/person")
    brand_name_zh:        Optional[str] = Field(None, max_length=100)
    brand_name_en:        Optional[str] = Field(None, max_length=100)
    contact_email:        Optional[EmailStr] = None
    contact_phone:        Optional[str] = Field(None, max_length=20)
    contact_person:       Optional[str] = Field(None, max_length=50)
    store_phone:          Optional[str] = Field(None, max_length=20)
    store_address:        Optional[str] = Field(None, max_length=200)
    payment_methods:      List[str] = Field(default_factory=list, description="['cc','apple','line','ipass','green']")
    payment_form_submitted: bool = False


# ── Step 3: 發票方案 ─────────────────────────────────────────────
class Step3InvoiceSchema(BaseModel):
    invoice_type:    str = 'miezo'
    invoice_plan:    Optional[InvoicePlan] = None
    contract_years:  Optional[int] = Field(None, ge=1, le=3)
    invoice_year_fee: Optional[int] = None
    setup_fee:       Optional[int] = None


# ── Step 4: 加值服務 ─────────────────────────────────────────────
class Step4AddonSchema(BaseModel):
    addon_print_invoice: bool = False
    addon_pdf_send:      bool = False
    addon_multi_channel: bool = False


# ── Step 5: 通知方式 ─────────────────────────────────────────────
class Step5NotifySchema(BaseModel):
    notify_email: bool = False
    notify_line:  bool = False
    notify_sms:   bool = False
    sms_plan:     Optional[str] = Field(None, max_length=10)


# ── Step 6: 確認送出 ─────────────────────────────────────────────
class Step6SubmitSchema(BaseModel):
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
    contact_person:   Optional[str]
    store_phone:      Optional[str]
    store_address:    Optional[str]
    payment_methods:  List[str]
    invoice_plan:     Optional[str]
    contract_years:   int
    invoice_year_fee: int
    setup_fee:        int
    addon_print_invoice: bool
    addon_pdf_send:   bool
    addon_multi_channel: bool
    notify_email:     bool
    notify_line:      bool
    notify_sms:       bool
    sms_plan:         Optional[str]
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
    contact_person:     Optional[str]
    store_phone:        Optional[str]
    store_address:      Optional[str]
    invoice_year_fee:   int
    setup_fee:          int
    addon_print_invoice: bool
    addon_pdf_send:     bool
    addon_multi_channel: bool
    notify_email:       bool
    notify_line:        bool
    notify_sms:         bool
    sms_plan:           Optional[str]
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
