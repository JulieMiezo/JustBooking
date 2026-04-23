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

    print("Migration 完成")

if __name__ == "__main__":
    run()
