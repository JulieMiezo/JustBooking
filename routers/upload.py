import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import ClientApplication, ApplicationDocument, DocumentType
from schemas import MessageResponse
from config import settings

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif",
    "application/pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

DOC_TYPE_LABELS = {
    "biz":   "營業登記文件",
    "id":    "身分證件",
    "bank":  "銀行存摺封面",
    "logo":  "Logo 圖檔",
    "scene": "場域形象圖",
}


def save_local(file_content: bytes, filename: str) -> str:
    """儲存到本機 uploads/ 目錄"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(file_content)
    return filepath


def save_to_gcs(file_content: bytes, destination: str) -> str:
    """上傳到 Google Cloud Storage（需設定 GCS_BUCKET_NAME）"""
    try:
        from google.cloud import storage
        client = storage.Client(project=settings.GCS_PROJECT_ID)
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(destination)
        blob.upload_from_string(file_content)
        return f"gs://{settings.GCS_BUCKET_NAME}/{destination}"
    except ImportError:
        raise HTTPException(status_code=500, detail="GCS 套件未安裝，請使用本機儲存")


@router.post("/{tax_id}/{doc_type}", response_model=MessageResponse)
async def upload_document(
    tax_id:   str,
    doc_type: str,
    file:     UploadFile = File(...),
    db:       Session    = Depends(get_db),
):
    """
    上傳文件
    - tax_id: 客戶統編
    - doc_type: biz / id / bank / logo / scene
    """
    # 驗證 doc_type
    if doc_type not in DOC_TYPE_LABELS:
        raise HTTPException(status_code=400, detail=f"不支援的文件類型: {doc_type}")

    # 找申請
    app = db.query(ClientApplication).filter(ClientApplication.tax_id == tax_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="找不到此統編的申請")

    # 驗證 MIME
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支援的檔案格式 {file.content_type}，僅接受 JPG/PNG/PDF"
        )

    # 讀取並檢查大小
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="檔案大小超過 10MB 限制")

    # 產生唯一檔名
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    unique_name = f"{tax_id}_{doc_type}_{uuid.uuid4().hex}{ext}"

    # 儲存
    if settings.GCS_BUCKET_NAME:
        storage_path = save_to_gcs(content, f"onboarding/{tax_id}/{unique_name}")
    else:
        storage_path = save_local(content, unique_name)

    # 更新或新增資料庫記錄
    existing_doc = db.query(ApplicationDocument).filter(
        ApplicationDocument.application_id == app.id,
        ApplicationDocument.doc_type == DocumentType(doc_type),
    ).first()

    if existing_doc:
        existing_doc.original_name = file.filename
        existing_doc.storage_path  = storage_path
        existing_doc.file_size     = len(content)
        existing_doc.mime_type     = file.content_type
    else:
        doc = ApplicationDocument(
            application_id = app.id,
            doc_type       = DocumentType(doc_type),
            original_name  = file.filename,
            storage_path   = storage_path,
            file_size      = len(content),
            mime_type      = file.content_type,
        )
        db.add(doc)

    db.commit()
    label = DOC_TYPE_LABELS[doc_type]
    return MessageResponse(message=f"{label} 上傳成功")
