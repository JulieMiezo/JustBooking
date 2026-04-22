from sqlalchemy import (
    Column, Integer, String, Text, Enum, DateTime,
    Boolean, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ── Enums ──────────────────────────────────────────────────────
class ApplicationStatus(str, enum.Enum):
    pending     = "pending"      # 待處理
    in_progress = "in_progress"  # 進行中
    reviewing   = "reviewing"    # 審核中
    approved    = "approved"     # 已完成
    rejected    = "rejected"     # 需修正


class InvoicePlan(str, enum.Enum):
    A = "A"  # 500張/月  $6,600/年
    B = "B"  # 1000張/月 $9,900/年
    C = "C"  # 3000張/月 $13,200/年
    D = "D"  # 5000張/月 $16,500/年
    E = "E"  # 10000張/月 $19,800/年
    F = "F"  # 15000張/月 $23,100/年
    G = "G"  # 20000張/月 $26,400/年


# ── Admin User ─────────────────────────────────────────────────
class AdminUser(Base):
    __tablename__ = "admin_users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name  = Column(String(100), nullable=False, default="管理員")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())


# ── Client Application ──────────────────────────────────────────
class ClientApplication(Base):
    __tablename__ = "client_applications"

    id              = Column(Integer, primary_key=True, index=True)

    # 基本資訊（從金流表單取得）
    tax_id          = Column(String(8), unique=True, nullable=False, index=True, comment="統一編號")
    brand_name_zh   = Column(String(100), comment="品牌中文名稱")
    brand_name_en   = Column(String(100), comment="品牌英文名稱")
    contact_email   = Column(String(150), comment="客服信箱")
    contact_phone   = Column(String(20), comment="客服電話")
    contact_person  = Column(String(50), comment="聯絡人")
    store_phone     = Column(String(20), comment="商店電話")
    store_address   = Column(String(200), comment="營業地址")

    # 金流申請
    payment_methods = Column(JSON, default=list, comment="申請金流項目 ['cc','apple','line',...]")
    payment_form_submitted = Column(Boolean, default=False, comment="藍新表單是否已填")

    # 發票方案
    invoice_plan    = Column(Enum(InvoicePlan), nullable=True, comment="發票方案 A-G")
    contract_years  = Column(Integer, default=1, comment="合約年限 1/2/3")
    invoice_year_fee = Column(Integer, default=0, comment="年費")
    setup_fee       = Column(Integer, default=3000, comment="設定費")

    # 加值服務
    addon_print_invoice = Column(Boolean, default=False, comment="列印中獎發票")
    addon_pdf_send      = Column(Boolean, default=False, comment="統編PDF寄送")
    addon_multi_channel = Column(Boolean, default=False, comment="多通路整合")

    # 申請狀態
    status          = Column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.in_progress,
        nullable=False,
        index=True,
    )
    current_step    = Column(Integer, default=1, comment="目前步驟 1-5")
    admin_note      = Column(Text, comment="後台備註")

    # 時間戳
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at    = Column(DateTime(timezone=True), nullable=True, comment="送出申請時間")

    # 關聯
    documents       = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")


# ── Document Uploads ────────────────────────────────────────────
class DocumentType(str, enum.Enum):
    biz   = "biz"    # 營業登記文件
    id    = "id"     # 身分證
    bank  = "bank"   # 銀行存摺封面
    logo  = "logo"   # Logo
    scene = "scene"  # 場域形象圖


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    id              = Column(Integer, primary_key=True, index=True)
    application_id  = Column(Integer, ForeignKey("client_applications.id"), nullable=False, index=True)
    doc_type        = Column(Enum(DocumentType), nullable=False, comment="文件類型")
    original_name   = Column(String(255), comment="原始檔名")
    storage_path    = Column(String(500), comment="儲存路徑（GCS 或本機）")
    file_size       = Column(Integer, comment="檔案大小 bytes")
    mime_type       = Column(String(100), comment="MIME type")
    uploaded_at     = Column(DateTime(timezone=True), server_default=func.now())

    application     = relationship("ClientApplication", back_populates="documents")
