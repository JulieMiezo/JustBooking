from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database import get_db
from models import ClientApplication, ApplicationStatus, AdminUser
from schemas import ApplicationListItem, ApplicationDetail, StatusUpdateSchema, MessageResponse
from routers.auth import get_current_admin

router = APIRouter()


def require_admin(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AdminUser:
    """從 Authorization header 取得並驗證管理員身份"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="請先登入")
    token = authorization.split(" ", 1)[1]
    return get_current_admin(token, db)


# ── 客戶列表 ─────────────────────────────────────────────────────
@router.get("/applications", response_model=List[ApplicationListItem])
def list_applications(
    status:   Optional[str]  = Query(None, description="篩選狀態"),
    search:   Optional[str]  = Query(None, description="搜尋統編/品牌名/信箱"),
    page:     int            = Query(1, ge=1),
    per_page: int            = Query(50, ge=1, le=200),
    db:       Session        = Depends(get_db),
    _:        AdminUser      = Depends(require_admin),
):
    """取得所有客戶申請清單（支援篩選與搜尋）"""
    query = db.query(ClientApplication)

    if status and status != "all":
        try:
            query = query.filter(ClientApplication.status == ApplicationStatus(status))
        except ValueError:
            pass

    if search:
        like = f"%{search}%"
        query = query.filter(
            ClientApplication.tax_id.like(like) |
            ClientApplication.brand_name_zh.like(like) |
            ClientApplication.brand_name_en.like(like) |
            ClientApplication.contact_email.like(like)
        )

    total = query.count()
    apps = (
        query
        .order_by(ClientApplication.updated_at.desc(), ClientApplication.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return apps


# ── 客戶詳情 ─────────────────────────────────────────────────────
@router.get("/applications/{app_id}", response_model=ApplicationDetail)
def get_application(
    app_id: int,
    db:     Session   = Depends(get_db),
    _:      AdminUser = Depends(require_admin),
):
    app = db.query(ClientApplication).filter(ClientApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="找不到此申請")
    return app


# ── 更新狀態 ─────────────────────────────────────────────────────
@router.patch("/applications/{app_id}/status", response_model=MessageResponse)
def update_status(
    app_id:  int,
    payload: StatusUpdateSchema,
    db:      Session   = Depends(get_db),
    admin:   AdminUser = Depends(require_admin),
):
    """核准 / 退回申請，可附加備註"""
    app = db.query(ClientApplication).filter(ClientApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="找不到此申請")

    app.status = payload.status
    if payload.admin_note is not None:
        app.admin_note = payload.admin_note

    db.commit()

    status_labels = {
        "approved": "已核准",
        "rejected": "已退回",
        "reviewing": "審核中",
        "in_progress": "進行中",
    }
    label = status_labels.get(payload.status.value, payload.status.value)
    return MessageResponse(message=f"申請狀態已更新為「{label}」")


# ── 統計數字 ─────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(
    db: Session   = Depends(get_db),
    _:  AdminUser = Depends(require_admin),
):
    """取得後台統計數字"""
    total      = db.query(ClientApplication).count()
    reviewing  = db.query(ClientApplication).filter(ClientApplication.status == ApplicationStatus.reviewing).count()
    approved   = db.query(ClientApplication).filter(ClientApplication.status == ApplicationStatus.approved).count()
    rejected   = db.query(ClientApplication).filter(ClientApplication.status == ApplicationStatus.rejected).count()
    in_progress = db.query(ClientApplication).filter(ClientApplication.status == ApplicationStatus.in_progress).count()

    return {
        "total":       total,
        "reviewing":   reviewing,
        "approved":    approved,
        "rejected":    rejected,
        "in_progress": in_progress,
    }
