"""检查 collector_tasks 表的列"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect
from app.core.database import engine

inspector = inspect(engine)
columns = inspector.get_columns("collector_tasks")

print("collector_tasks 表的列：")
for col in columns:
    print(f"  - {col['name']}: {col['type']}")
