"""
数据库迁移脚本：添加缺失的列
运行方式：python migrate_add_missing_columns.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect, text
from app.core.database import engine, SessionLocal


def add_missing_columns():
    """检查并添加缺失的列"""
    inspector = inspect(engine)
    
    with SessionLocal() as db:
        # 检查 collector_tasks 表
        if "collector_tasks" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("collector_tasks")]
            
            # 需要添加的列
            missing_columns = []
            if "collect_type" not in columns:
                missing_columns.append(("collect_type", "VARCHAR(32) NOT NULL DEFAULT 'search'"))
            if "limit_count" not in columns:
                missing_columns.append(("limit_count", "INTEGER NOT NULL DEFAULT 20"))
            
            # 添加缺失的列
            for col_name, col_def in missing_columns:
                try:
                    sql = text(f"ALTER TABLE collector_tasks ADD COLUMN {col_name} {col_def}")
                    db.execute(sql)
                    db.commit()
                    print(f"✅ 已添加列: collector_tasks.{col_name}")
                except Exception as e:
                    print(f"❌ 添加列失败 collector_tasks.{col_name}: {e}")
                    db.rollback()
        else:
            print("⚠️  表 collector_tasks 不存在，请先运行 init_db() 创建表")
        
        # 检查其他可能缺失的列
        print("\n检查所有表结构...")
        for table_name in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            print(f"📋 {table_name}: {len(columns)} 列")


if __name__ == "__main__":
    print("开始数据库迁移...\n")
    add_missing_columns()
    print("\n✅ 迁移完成！")
