"""
一次性 migration：為 client_applications 新增三個欄位
執行方式：python migrate.py
"""
from sqlalchemy import text, inspect
from database import engine

NEW_COLUMNS = [
    ("contact_person", "VARCHAR(50) NULL COMMENT '聯絡人'"),
    ("store_phone",    "VARCHAR(20) NULL COMMENT '商店電話'"),
    ("store_address",  "VARCHAR(200) NULL COMMENT '營業地址'"),
    ("invoice_type",   "VARCHAR(20) NULL COMMENT '發票類型 miezo/neweb/ecpay/none'"),
    ("applicant_type", "VARCHAR(10) NULL COMMENT '申請人類型 company/person'"),
    ("notify_email",   "TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Email 通知'"),
    ("notify_line",    "TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'LINE 通知'"),
    ("notify_sms",     "TINYINT(1) NOT NULL DEFAULT 0 COMMENT '簡訊通知'"),
    ("sms_plan",       "VARCHAR(10) NULL COMMENT '簡訊方案 3000/6000/12000'"),
]

def run():
    insp = inspect(engine)
    existing = {col["name"] for col in insp.get_columns("client_applications")}

    with engine.begin() as conn:
        for col_name, col_def in NEW_COLUMNS:
            if col_name in existing:
                print(f"  ✓ {col_name} 已存在，略過")
            else:
                sql = f"ALTER TABLE client_applications ADD COLUMN {col_name} {col_def}"
                conn.execute(text(sql))
                print(f"  + {col_name} 已新增")

        # 擴充 tax_id 欄位長度以支援身分證字號（10碼）
        tax_col = next((c for c in insp.get_columns("client_applications") if c["name"] == "tax_id"), None)
        if tax_col:
            conn.execute(text(
                "ALTER TABLE client_applications MODIFY COLUMN tax_id VARCHAR(20) NOT NULL COMMENT '統編或身分證字號'"
            ))
            print("  ✓ tax_id 已擴充為 VARCHAR(20)")

    print("Migration 完成")

if __name__ == "__main__":
    run()
