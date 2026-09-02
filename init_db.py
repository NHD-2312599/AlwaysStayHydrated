"""
init_db.py — Khởi tạo achievements.db cho hệ thống badge
=========================================================
Chạy khi cần tạo / cập nhật achievements.db (KHÔNG đụng flashcard.db):

    python init_db.py

Script này sẽ:
  1. Tạo file SQLite tại instance/achievements.db (nếu chưa có)
  2. Tạo 3 bảng achievement (user_stats, achievements, user_achievements)
  3. Seed / đồng bộ badge từ ACHIEVEMENT_SEED (idempotent)
"""

import os
import sys

try:
    from flask import Flask
except ImportError:
    print("❌  Thiếu thư viện. Chạy: pip install flask flask-sqlalchemy")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from flashcard_models import db
    from achievement_db import configure_achievement_bind, ACHIEVEMENT_BIND, get_achievement_db_path
    from achievement_models import (
        Achievement,
        init_achievement_db,
    )
except ImportError as e:
    print(f"❌  Không import được module: {e}")
    sys.exit(1)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
configure_achievement_bind(app, BASE_DIR)
db.init_app(app)

with app.app_context():
    ach_path = get_achievement_db_path(BASE_DIR)
    print(f"📂  Achievement DB: {ach_path}")

    init_achievement_db(app)

    total = Achievement.query.count()
    print(f"🏆  Tổng {total} badge trong DB.")

    engine = db.get_engine(app, bind=ACHIEVEMENT_BIND)
    tables = db.engine.dialect.get_table_names(engine.connect())
    print(f"📋  Các bảng trong achievements.db: {', '.join(sorted(tables))}")

print("\n🎉  Khởi tạo achievements.db thành công!")
