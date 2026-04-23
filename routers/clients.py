from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import ClientApplication, ApplicationStatus
from schemas import (
    Step1PaymentSchema, Step3InvoiceSchema, Step4AddonSchema,
    ApplicationQueryOut, MessageResponse,
)

router = APIRouter()

INVOICE_YEAR_FEE = {
    "A": 6600, "B": 9900, "C": 13200, "D": 16500,
    "E": 19800, "F": 23100, "G": 26400,
}


def get_or_404(db: Session, tax_id: str) -> ClientApplication:
    app = db.query(ClientApplication).filter(
        ClientApplication.tax_id == tax_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="查無此統編的申請紀錄")
    return app


# ── 查詢進度（公開）─────────────────────────────────────────────
@router.get("/query/{tax_id}", response_model=ApplicationQueryOut)
def query_progress(tax_id: str, db: Session = Depends(get_db)):
    """客戶用統編查詢申請進度"""
    return get_or_404(db, tax_id)


# ── Step 1: 金流申請 ────────────────────────────────────────────
@router.post("/step1", response_model=MessageResponse)
def submit_step1(payload: Step1PaymentSchema, db: Session = Depends(get_db)):
    """建立或更新基本資訊與金流申請"""
    existing = db.query(ClientApplication).filter(
        ClientApplication.tax_id == payload.tax_id
    ).first()

    if existing:
        # 更新
        existing.brand_name_zh = payload.brand_name_zh
        existing.brand_name_en = payload.brand_name_en
        existing.contact_email  = str(payload.contact_email) if payload.contact_email else None
        existing.contact_phone  = payload.contact_phone
        existing.contact_person = payload.contact_person
        existing.store_phone    = payload.store_phone
        existing.store_address  = payload.store_address
        existing.payment_methods = payload.payment_methods
        existing.payment_form_submitted = payload.payment_form_submitted
        existing.current_step = max(existing.current_step, 2)
        if existing.status == ApplicationStatus.pending:
            existing.status = ApplicationStatus.in_progress
        db.commit()
        return MessageResponse(message="金流資料已更新")
    else:
        # 新建
        app = ClientApplication(
            tax_id=payload.tax_id,
            brand_name_zh=payload.brand_name_zh,
            brand_name_en=payload.brand_name_en,
            contact_email=str(payload.contact_email) if payload.contact_email else None,
            contact_phone=payload.contact_phone,
            contact_person=payload.contact_person,
            store_phone=payload.store_phone,
            store_address=payload.store_address,
            payment_methods=payload.payment_methods,
            payment_form_submitted=payload.payment_form_submitted,
            status=ApplicationStatus.in_progress,
            current_step=2,
        )
        db.add(app)
        db.commit()
        return MessageResponse(message="申請已建立，請繼續完成後續步驟")


# ── Step 2: 上傳文件（進度更新）────────────────────────────────
# 實際上傳由 upload router 處理，這裡只更新步驟進度
@router.post("/step2/{tax_id}", response_model=MessageResponse)
def complete_step2(tax_id: str, db: Session = Depends(get_db)):
    """標記文件上傳步驟完成"""
    app = get_or_404(db, tax_id)
    app.current_step = max(app.current_step, 3)
    db.commit()
    return MessageResponse(message="文件上傳步驟完成")


# ── Step 3: 發票方案 ────────────────────────────────────────────
@router.post("/step3/{tax_id}", response_model=MessageResponse)
def submit_step3(tax_id: str, payload: Step3InvoiceSchema, db: Session = Depends(get_db)):
    """儲存發票方案選擇"""
    app = get_or_404(db, tax_id)
    app.invoice_type = payload.invoice_type
    if payload.invoice_type == 'miezo' and payload.invoice_plan:
        app.invoice_plan     = payload.invoice_plan
        app.contract_years   = payload.contract_years
        app.invoice_year_fee = payload.invoice_year_fee or 0
        app.setup_fee        = payload.setup_fee if payload.setup_fee is not None else 3000
        app.current_step     = max(app.current_step, 4)
    else:
        app.current_step     = max(app.current_step, 5)
    db.commit()
    return MessageResponse(message="發票資訊已儲存")


# ── Step 4: 加值服務 ────────────────────────────────────────────
@router.post("/step4/{tax_id}", response_model=MessageResponse)
def submit_step4(tax_id: str, payload: Step4AddonSchema, db: Session = Depends(get_db)):
    """儲存加值服務選擇"""
    app = get_or_404(db, tax_id)
    app.addon_print_invoice = payload.addon_print_invoice
    app.addon_pdf_send      = payload.addon_pdf_send
    app.addon_multi_channel = payload.addon_multi_channel
    app.current_step        = max(app.current_step, 5)
    db.commit()
    return MessageResponse(message="加值服務已儲存")


# ── Step 5: 確認送出 ────────────────────────────────────────────
@router.post("/step5/{tax_id}", response_model=MessageResponse)
def submit_final(tax_id: str, db: Session = Depends(get_db)):
    """最終送出申請"""
    app = get_or_404(db, tax_id)

    if app.status in (ApplicationStatus.approved, ApplicationStatus.reviewing):
        raise HTTPException(status_code=400, detail="此申請已送出或審核中，無法重複送出")

    app.status       = ApplicationStatus.reviewing
    app.current_step = 5
    app.submitted_at = datetime.utcnow()
    db.commit()
    return MessageResponse(message="申請已送出，我們將盡快審核並與您聯繫")
