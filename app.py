import json
import random
import os
from functools import wraps
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.security import check_password_hash  # Keep for backward compatibility
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import shutil, pathlib
from flashcard_models import db, Tab, Card, CardStatus, ExamReviewStatus, init_db
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Copy fonts dung duong dan tuyet doi (tranh loi CWD tren PythonAnywhere)
_src_fonts = pathlib.Path(BASE_DIR) / 'BD Lifeless Grotesk'
_dst_fonts = pathlib.Path(BASE_DIR) / 'static' / 'fonts'
_dst_fonts.mkdir(parents=True, exist_ok=True)
if _src_fonts.exists():
    for p in _src_fonts.rglob('*.woff2'):
        shutil.copy2(p, _dst_fonts)

FLASHCARD_DB_PATH = os.path.join(BASE_DIR, "instance", "flashcard.db")
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{FLASHCARD_DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False},
    'pool_pre_ping': True,
    'pool_recycle': 30,
}
print("Flashcard DB:", FLASHCARD_DB_PATH)

db.init_app(app)
init_db(app)


CORS(app, resources={r"/api/*": {"origins": "*"}})

# async_mode="threading": không cần cài eventlet/gevent, chạy được cả trên
# PythonAnywhere (dùng long-polling nếu server không hỗ trợ websocket thật).
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Trang cần session — không cache HTML theo user cũ
_NO_CACHE_HTML_PREFIXES = (
    "/home", "/flashcard", "/exam_library", "/exam/",
)

@app.after_request
def after_request(response):
    db.session.expire_all()  # Xoá cache SQLAlchemy, đảm bảo request sau luôn đọc data mới từ DB
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')

    path = request.path
    if path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Vary"] = "Cookie"
    elif path == "/home" or any(path.startswith(p) for p in _NO_CACHE_HTML_PREFIXES):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Vary"] = "Cookie"

    return response

with open(os.path.join(BASE_DIR, "khai_huyen_data.json"), encoding="utf-8") as f:
    BIBLE_DATA = json.load(f)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

# ─── User helpers ────────────────────────────────────────────────────────────

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ─── Password hashing helpers (Argon2) ──────────────────────────────────────

ph = PasswordHasher()

def hash_password(password):
    """Hash password using Argon2"""
    return ph.hash(password)

def verify_password(pw_hash, password):
    """
    Verify password. Supports both Argon2 (new) and Scrypt (old).
    Auto-upgrades scrypt to argon2 if needed.
    Returns: (is_valid, needs_upgrade)
    """
    try:
        # Try Argon2 first
        ph.verify(pw_hash, password)
        return True, False
    except (VerifyMismatchError, InvalidHashError):
        # Argon2 failed, try Scrypt (legacy)
        try:
            if check_password_hash(pw_hash, password):
                return True, True  # Valid scrypt, needs upgrade
        except:
            pass
        return False, False  # Invalid password

# ─── Token auth ──────────────────────────────────────────────────────────────

serializer = URLSafeTimedSerializer(app.secret_key)

def generate_api_token(username, role="view"):
    return serializer.dumps({"user": username, "role": role})

def verify_api_token(token, max_age=86400):
    try:
        return serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

def get_api_user():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        data = verify_api_token(auth_header.split("Bearer ", 1)[1].strip())
        if data:
            return data["user"]
    return session.get("user")

def get_api_role():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        data = verify_api_token(auth_header.split("Bearer ", 1)[1].strip())
        if data:
            return data.get("role", "view")
    return session.get("flashcard_role", "view")

# ─── Auth decorators ─────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if session.get("user"):
            return f(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("login", next=request.path))
    return wrapped

def hybrid_api_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            data = verify_api_token(auth_header.split("Bearer ", 1)[1].strip())
            if data:
                return f(data["user"], *args, **kwargs)
        if session.get("user"):
            return f(session["user"], *args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 401
    return wrapped

def flashcard_api_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not get_api_user():
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapped

def flashcard_admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        user = get_api_user()
        if not user:
            return jsonify({"error": "Unauthorized"}), 401
        if get_api_role() != "admin":
            return jsonify({"error": "Forbidden - admin access required"}), 403
        return f(*args, **kwargs)
    return wrapped

# ─── Bible helpers ───────────────────────────────────────────────────────────

def make_blank_question(verse_text, level=1):
    """
    Tạo câu hỏi điền vào chỗ trống theo độ khó:
      Lv1: Điền 3–5 từ (cụm từ ngắn)
      Lv2: Điền 10–15 từ (cụm từ dài)
      Lv3: Điền toàn bộ câu (câu hỏi chỉ hiện tham chiếu, người dùng tự nhớ)
    """
    words = verse_text.split()
    total = len(words)

    # ── Level 3: điền toàn bộ câu ─────────────────────────────
    if level == 3:
        if total < 3:
            return None, None
        # Câu hỏi trả về rỗng để client hiển thị "Hãy điền toàn bộ câu..."
        # answer là toàn bộ câu gốc
        return "", verse_text

    # ── Level 2: điền 10–15 từ ────────────────────────────────
    if level == 2:
        # Nếu câu quá ngắn, fallback về Lv1
        if total < 12:
            level = 1
        else:
            min_blank = min(10, total - 2)
            max_blank = min(15, total - 2)
            blank_len = random.randint(min_blank, max_blank)
            max_start = total - blank_len - 1
            if max_start < 1:
                return None, None
            start = random.randint(1, max_start)
            answer = " ".join(words[start:start + blank_len])
            blanked = words[:start] + ["___________"] + words[start + blank_len:]
            return " ".join(blanked), answer

    # ── Level 1: điền 3–5 từ ──────────────────────────────────
    if total < 5:
        return None, None
    blank_len = random.randint(3, min(5, max(3, total // 3)))
    max_start = total - blank_len - 1
    if max_start < 1:
        return None, None
    start = random.randint(1, max_start)
    answer = " ".join(words[start:start + blank_len])
    blanked = words[:start] + ["___________"] + words[start + blank_len:]
    return " ".join(blanked), answer

from multiplayer import register_multiplayer
register_multiplayer(socketio, BIBLE_DATA, make_blank_question)

# ─── Stats helper ────────────────────────────────────────────────────────────

def _calculate_stats(user):
    total = Card.query.count()
    passed = CardStatus.query.filter_by(user_id=user, status='g').count()
    review = CardStatus.query.filter_by(user_id=user, status='r').count()
    hard   = CardStatus.query.filter_by(user_id=user, status='h').count()
    return {
        'total': total, 'passed': passed, 'review': review, 'hard': hard,
        'not_studied': total - passed - review - hard,
        'percentage': round((passed / total * 100) if total > 0 else 0, 1)
    }

# ─── Web routes ──────────────────────────────────────────────────────────────

@app.route('/')
def landing():
    return render_template("LandingPage.html")

@app.route('/download')
def download_page():
    return render_template("download.html")

@app.route('/home')
@login_required
def index():
    return render_template("index.html")

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Lưu feedback từ Landing Page vào file feedback.txt"""
    data = request.json or {}
    content = data.get("message", "").strip()
    if not content:
        return jsonify({"error": "Nội dung feedback không được để trống."}), 400

    feedback_dir = os.path.join(BASE_DIR, "feedback")
    os.makedirs(feedback_dir, exist_ok=True)
    feedback_file = os.path.join(feedback_dir, "feedback.txt")

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = session.get("user", "Khách (chưa đăng nhập)")

    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ({user})\n{content}\n{'-'*50}\n")

    return jsonify({"message": "Đã lưu feedback thành công!"}), 200

@app.route("/flashcard")
@login_required
def flashcard():
    if not session.get("flashcard_role"):
        return redirect(url_for("flashcard_login"))
    return render_template("flashcard.html",
                           user=session["user"],
                           role=session["flashcard_role"])

@app.route("/register", methods=["GET", "POST"])
def register():
    msg = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            msg = "Vui lòng nhập tên đăng nhập và mật khẩu."
        else:
            users = load_users()
            if username in users:
                msg = "Tài khoản đã tồn tại."
            else:
                users[username] = {"pw": hash_password(password)}
                save_users(users)
                session["user"] = username
                return redirect(url_for("index"))
    return render_template("register.html", msg=msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        user = users.get(username)
        if not user:
            msg = "Tên đăng nhập hoặc mật khẩu không đúng."
        else:
            is_valid, needs_upgrade = verify_password(user.get("pw", ""), password)
            if not is_valid:
                msg = "Tên đăng nhập hoặc mật khẩu không đúng."
            else:
                # Auto-upgrade scrypt passwords to argon2
                if needs_upgrade:
                    users[username]["pw"] = hash_password(password)
                    save_users(users)
                session["user"] = username
                return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html", msg=msg)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login", fresh=1))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    msg = None
    success = False
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        new_pw   = request.form.get("new_password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()
        if not username or not new_pw or not confirm:
            msg = "Vui lòng điền đầy đủ tất cả trường."
        elif new_pw != confirm:
            msg = "Mật khẩu xác nhận không khớp."
        elif len(new_pw) < 6:
            msg = "Mật khẩu phải có ít nhất 6 ký tự."
        else:
            users = load_users()
            if username not in users:
                msg = "Tài khoản này không tồn tại."
            else:
                users[username]["pw"] = hash_password(new_pw)
                save_users(users)
                success = True
                msg = "Mật khẩu đã được cập nhật thành công! Vui lòng đăng nhập lại."
    return render_template("forgot_password.html", msg=msg, success=success)

@app.route("/flashcard/login", methods=["GET", "POST"])
@login_required
def flashcard_login():
    msg = None
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if password == "donganadmin":
            session["flashcard_role"] = "admin"
            return redirect(url_for("flashcard"))
        elif password == "dongan":
            session["flashcard_role"] = "view"
            return redirect(url_for("flashcard"))
        else:
            msg = "Mật khẩu không đúng. Vui lòng đăng nhập lại."
    return render_template("flashcard_login.html", msg=msg)

@app.route("/flashcard/logout")
def flashcard_logout():
    session.pop("flashcard_role", None)
    return redirect(url_for("flashcard_login"))

# ─── PWA routes ──────────────────────────────────────────────────────────────

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'manifest.json')

@app.route('/sw.js')
def service_worker():
    response = send_from_directory(os.path.join(BASE_DIR, 'static'), 'sw.js')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/offline.html')
def offline():
    return render_template('offline.html')

# ─── Bible API ───────────────────────────────────────────────────────────────

@app.route("/api/chapters")
@hybrid_api_required
def get_chapters(user):
    info = {
        ch: {"count": len(verses), "max_verse": max(v["verse"] for v in verses)}
        for ch, verses in BIBLE_DATA.items() if verses
    }
    return jsonify(info)

@app.route("/api/question")
@hybrid_api_required
def get_question(user):
    chapter       = request.args.get("chapter", "random")
    start_verse   = int(request.args.get("start_verse", 1))
    end_verse     = int(request.args.get("end_verse", 9999))
    mode          = request.args.get("mode", "random")
    current_verse = request.args.get("current_verse")
    get_all       = request.args.get("get_all", "false").lower() == "true"
    # Flutter gửi 'difficulty', web gửi 'level' — đọc cả hai, ưu tiên 'difficulty'
    level         = int(request.args.get("difficulty", request.args.get("level", 1)))

    ch = str(random.randint(1, 22)) if chapter == "random" else str(int(chapter))
    verses = BIBLE_DATA.get(ch, [])
    if not verses:
        return jsonify({"error": "Không có dữ liệu"}), 400

    filtered = [v for v in verses if start_verse <= v["verse"] <= end_verse]
    if not filtered:
        return jsonify({"error": f"Không có câu nào trong khoảng {start_verse}-{end_verse}"}), 400

    if get_all:
        return jsonify([
            {"chapter": int(ch), "verse": v["verse"],
             "question": q, "answer": a, "full_verse": v["text"], "level": level}
            for v in filtered
            for q, a in [make_blank_question(v["text"], level)]
            if q is not None
        ])

    # ── Chọn câu theo chế độ ──────────────────────────────────
    if mode == "sequential" and current_verse is not None:
        try:
            curr = int(current_verse)
            # Tìm đúng câu có verse == curr; nếu không có thì lấy câu gần nhất >= curr
            verse_obj = next(
                (v for v in filtered if v["verse"] == curr),
                next((v for v in filtered if v["verse"] >= curr), filtered[0])
            )
        except Exception:
            verse_obj = random.choice(filtered)
    else:
        verse_obj = random.choice(filtered)

    q, a = make_blank_question(verse_obj["text"], level)
    if q is None:
        # Fallback: thử câu khác nếu câu quá ngắn
        verse_obj = random.choice(filtered)
        q, a = make_blank_question(verse_obj["text"], level)
        if q is None:
            return jsonify({"error": "Câu quá ngắn để tạo câu hỏi"}), 400

    # ── Level 3: trả về prompt đặc biệt thay vì câu trống ────
    if level == 3:
        question_text = f"Hãy điền đúng toàn bộ câu Khải Huyền {ch}:{verse_obj['verse']}"
    else:
        question_text = q

    return jsonify({
        "chapter": int(ch), "verse": verse_obj["verse"],
        "question": question_text, "answer": a,
        "full_verse": verse_obj["text"], "level": level
    })

@app.route("/api/typing-question")
@hybrid_api_required
def get_typing_question(user):
    chapter     = request.args.get("chapter", "random")
    start_verse = int(request.args.get("start_verse", 1))
    end_verse   = int(request.args.get("end_verse", 9999))
    get_all     = request.args.get("get_all", "false").lower() == "true"

    ch = str(random.randint(1, 22)) if chapter == "random" else str(int(chapter))
    verses = BIBLE_DATA.get(ch, [])
    if not verses:
        return jsonify({"error": "Không có dữ liệu"}), 400

    filtered = [v for v in verses if start_verse <= v["verse"] <= end_verse]
    if not filtered:
        return jsonify({"error": f"Không có câu nào trong khoảng {start_verse}-{end_verse}"}), 400

    if get_all:
        return jsonify([{
            "chapter": int(ch), "verse": v["verse"],
            "text": v["text"], "word_count": len(v["text"].split())
        } for v in filtered])

    verse_obj = random.choice(filtered)
    return jsonify({
        "chapter": int(ch), "verse": verse_obj["verse"],
        "text": verse_obj["text"], "word_count": len(verse_obj["text"].split())
    })

@app.route("/api/check-typing", methods=["POST"])
@hybrid_api_required
def check_typing(user):
    data     = request.json or {}
    original = data.get("original", "").strip()
    typed    = data.get("typed", "").strip()
    time_sec = data.get("time_seconds", 0)
    # Client tự đếm số lần gõ hoàn hảo cùng 1 câu liên tiếp rồi gửi lên
    same_verse_streak = int(data.get("same_verse_perfect_streak", 0))
 
    if not original or not typed:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
 
    total   = max(len(original), len(typed))
    correct = sum(1 for i in range(min(len(original), len(typed)))
                  if original[i] == typed[i])
    is_perfect = (original == typed)
    accuracy   = round((correct / total * 100) if total > 0 else 0, 1)
    wpm        = round(len(original.split()) / ((time_sec / 60) or 1), 1)
 
    return jsonify({
        "is_perfect":        is_perfect,
        "accuracy":          accuracy,
        "wpm":               wpm,
        "time_seconds":      time_sec,
        "correct_chars":     correct,
        "total_chars":       total,
    })

# ─── Mobile API auth ─────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Tên đăng nhập và mật khẩu bắt buộc."}), 400
    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không đúng."}), 401
    is_valid, needs_upgrade = verify_password(user.get("pw", ""), password)
    if not is_valid:
        return jsonify({"error": "Tên đăng nhập hoặc mật khẩu không đúng."}), 401
    # Auto-upgrade scrypt passwords to argon2
    if needs_upgrade:
        users[username]["pw"] = hash_password(password)
        save_users(users)
    role = user.get("role", "view")
    return jsonify({"token": generate_api_token(username, role), "user": username, "role": role})

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Tên đăng nhập và mật khẩu bắt buộc."}), 400
    users = load_users()
    if username in users:
        return jsonify({"error": "Tài khoản đã tồn tại."}), 400
    users[username] = {"pw": hash_password(password), "role": "view"}
    save_users(users)
    return jsonify({"token": generate_api_token(username, "view"), "user": username, "role": "view"}), 201

@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.json or {}
    username = data.get("username", "").strip()
    new_pw   = data.get("new_password", data.get("password", "")).strip()
    if not username or not new_pw:
        return jsonify({"error": "Thiếu thông tin."}), 400
    users = load_users()
    if username not in users:
        return jsonify({"error": "Tài khoản không tồn tại."}), 404
    users[username]["pw"] = generate_password_hash(new_pw)
    save_users(users)
    return jsonify({"message": "Đặt lại mật khẩu thành công."})

# ─── Flashcard API ───────────────────────────────────────────────────────────

@app.route("/api/flashcard/check-auth")
def flashcard_check_auth():
    user = get_api_user()
    return jsonify({
        'authenticated': bool(user),
        'user': user,
        'role': get_api_role()
    })

@app.route("/api/flashcard/data")
@flashcard_api_required
def get_flashcard_data():
    db.session.expire_all()  # Đảm bảo luôn đọc dữ liệu mới nhất từ DB
    user = get_api_user()
    data = []
    for tab in Tab.query.order_by(Tab.created_at).all():
        tab_dict = {'id': tab.id, 'name': tab.name, 'cards': []}
        for card in tab.cards:
            cd = card.to_dict(include_statuses=False)
            s = CardStatus.query.filter_by(card_id=card.id, user_id=user).first()
            cd['status'] = s.status if s else ''
            tab_dict['cards'].append(cd)
        data.append(tab_dict)
    response = jsonify({'data': data, 'stats': _calculate_stats(user)})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/api/flashcard/stats")
@flashcard_api_required
def get_flashcard_stats():
    return jsonify(_calculate_stats(get_api_user()))

@app.route("/api/flashcard/tabs", methods=["POST"])
@flashcard_admin_required
def create_tab():
    name = (request.json or {}).get('name', '').strip()
    if not name:
        return jsonify({'error': 'Tab name required'}), 400
    import uuid
    tab = Tab(id=f"t{uuid.uuid4().hex[:8]}", name=name)
    db.session.add(tab)
    db.session.commit()
    return jsonify(tab.to_dict()), 201

@app.route("/api/flashcard/tabs/<tab_id>", methods=["PUT"])
@flashcard_admin_required
def update_tab(tab_id):
    tab = Tab.query.get(tab_id)
    if not tab:
        return jsonify({'error': 'Tab not found'}), 404
    new_name = (request.json or {}).get('name', '').strip()
    if new_name:
        tab.name = new_name
        db.session.commit()
    return jsonify(tab.to_dict())

@app.route("/api/flashcard/tabs/<tab_id>", methods=["DELETE"])
@flashcard_admin_required
def delete_tab(tab_id):
    tab = Tab.query.get(tab_id)
    if not tab:
        return jsonify({'error': 'Tab not found'}), 404
    Card.query.filter_by(tab_id=tab_id).delete()
    db.session.delete(tab)
    db.session.commit()
    return jsonify({'message': 'Tab deleted'}), 200

@app.route("/api/flashcard/cards", methods=["POST"])
@flashcard_admin_required
def create_card():
    data   = request.json or {}
    tab_id = data.get('tab_id', '').strip()
    ref    = data.get('ref', '').strip()
    title  = data.get('title', '').strip()
    if not tab_id or not ref or not title:
        return jsonify({'error': 'tab_id, ref, and title required'}), 400
    if not Tab.query.get(tab_id):
        return jsonify({'error': 'Tab not found'}), 404
    card = Card(id='c' + str(Card.query.count() + 1), tab_id=tab_id, ref=ref,
                title=title, verse=data.get('verse',''), analysis=data.get('analysis',''),
                speech=data.get('speech',''))
    db.session.add(card)
    db.session.commit()
    return jsonify(card.to_dict()), 201

@app.route("/api/flashcard/cards/<card_id>", methods=["PUT"])
@flashcard_admin_required
def update_card(card_id):
    card = Card.query.get(card_id)
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    for field in ('ref', 'title', 'verse', 'analysis', 'speech'):
        val = (request.json or {}).get(field)
        if val is not None:
            setattr(card, field, val.strip() if isinstance(val, str) else val)
    db.session.commit()
    return jsonify(card.to_dict())

@app.route("/api/flashcard/cards/<card_id>", methods=["DELETE"])
@flashcard_admin_required
def delete_card(card_id):
    card = Card.query.get(card_id)
    if not card:
        return jsonify({'error': 'Card not found'}), 404
    db.session.delete(card)
    db.session.commit()
    return jsonify({'message': 'Card deleted'}), 200

@app.route("/api/flashcard/cards/<card_id>/status", methods=["POST"])
def update_card_status(card_id):
    user = get_api_user()
    card = Card.query.get(card_id)
    if not card:
        return jsonify({'error': 'Card not found'}), 404
 
    new_status = (request.json or {}).get('status', '').strip()
    if new_status not in ('', 'g', 'r', 'h'):
        return jsonify({'error': 'Invalid status'}), 400
 
    # Lấy status cũ trước khi update
    s = CardStatus.query.filter_by(card_id=card_id, user_id=user).first()
    old_status = s.status if s else ''
 
    if s:
        s.status = new_status
    else:
        db.session.add(CardStatus(card_id=card_id, user_id=user, status=new_status))
    db.session.commit()
 
    return jsonify({
        'card_id':           card_id,
        'user_id':           user,
        'status':            new_status,
    })

@app.route("/api/sync")
@flashcard_api_required
def sync():
    return jsonify({"message": "Sync successful"})

@app.route('/download-apk')
def download_apk():
    return send_from_directory(
        '/home/AlwayStayHydrated/ASH/flutter_app/',
        'AlwaysStayHydrated-Demo.apk',
        as_attachment=True
    )

# ─── Exam / Kiểm Tra routes ──────────────────────────────────────────────────

EXAM_DIR = os.path.join(BASE_DIR, "Exam")

# Mật khẩu riêng cho từng học phần — id phải khớp với "id" trong file JSON
EXAM_PASSWORDS = {
    "tab1": "dongan_baithitotnghiep"
}


def load_exam_data():
    """
    Đọc tất cả file *.json trong thư mục Exam/ và gộp tabs.
    Thêm học phần mới: tạo file JSON mới + thêm mật khẩu vào EXAM_PASSWORDS.
    """
    tabs = []
    if not os.path.isdir(EXAM_DIR):
        return {"tabs": tabs}

    for filename in sorted(os.listdir(EXAM_DIR)):
        if not filename.lower().endswith(".json"):
            continue
        path = os.path.join(EXAM_DIR, filename)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            file_tabs = data.get("tabs") or []
            if not isinstance(file_tabs, list):
                print(f"[exam] Bỏ qua {filename}: 'tabs' không phải list")
                continue
            for tab in file_tabs:
                if not tab.get("id"):
                    print(f"[exam] Bỏ qua tab thiếu id trong {filename}")
                    continue
                if any(t["id"] == tab["id"] for t in tabs):
                    print(f"[exam] Trùng tab id '{tab['id']}' — bỏ qua bản trong {filename}")
                    continue
                tabs.append(tab)
        except Exception as e:
            print(f"[exam] Lỗi đọc {filename}: {e}")

    return {"tabs": tabs}


def get_exam_tab(tab_id):
    """Lấy đúng học phần từ nguồn bài thi, không dùng dữ liệu flashcard khác."""
    return next(
        (tab for tab in load_exam_data()["tabs"]
         if tab.get("id") == tab_id and tab_id in EXAM_PASSWORDS),
        None,
    )

@app.route("/multiplayer", endpoint="multiplayer")
@login_required
def multiplayer_home():
    return render_template("multiplayer_home.html", username=session.get("user"))

@app.route("/multiplayer/room/create")
@login_required
def multiplayer_room_create():
    # code=None -> template biết cần emit mp_create_room thay vì mp_join_room
    return render_template("multiplayer_room.html", room_code=None, username=session.get("user"))

@app.route("/multiplayer/room/<code>")
@login_required
def multiplayer_room(code):
    return render_template("multiplayer_room.html", room_code=code, username=session.get("user"))

@app.route("/exam_library")
@login_required
def exam_library():
    return render_template("exam_library.html", user=session["user"])

@app.route("/exam/<tab_id>")
@login_required
def exam(tab_id):
    # Kiểm tra đã xác thực password cho tab này chưa
    if not get_exam_tab(tab_id) or session.get(f"exam_auth_{tab_id}") != True:
        return redirect(url_for("exam_library"))
    exam_mode = request.args.get("mode", "full")
    if exam_mode not in {"full", "blank"}:
        exam_mode = "full"
    return render_template(
        "exam.html",
        tab_id=tab_id,
        exam_mode=exam_mode,
        user=session["user"],
    )

@app.route("/exam-review/<tab_id>")
@login_required
def exam_review(tab_id):
    if not get_exam_tab(tab_id) or session.get(f"exam_auth_{tab_id}") is not True:
        return redirect(url_for("exam_library"))
    return render_template("exam_review.html", tab_id=tab_id, user=session["user"])

def exam_api_required(f):
    """Giống login_required nhưng hỗ trợ cả Bearer token (app mobile)
    lẫn session cookie (web), dùng get_api_user() để lấy user."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not get_api_user():
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapped


def _issue_exam_token(user, tab_id):
    """Token có chữ ký, xác nhận user đã nhập đúng mật khẩu cho tab_id.
    Dùng cho client không giữ session cookie (app Flutter)."""
    return serializer.dumps({"user": user, "tab_id": tab_id}, salt="exam-tab-access")


def _has_exam_access(tab_id):
    """Đã mở khoá tab thi này chưa — qua session (web) hoặc X-Exam-Token (mobile)."""
    if session.get(f"exam_auth_{tab_id}") == True:
        return True
    token = request.headers.get("X-Exam-Token", "")
    if token:
        try:
            data = serializer.loads(token, salt="exam-tab-access", max_age=86400)
            if data.get("tab_id") == tab_id and data.get("user") == get_api_user():
                return True
        except (BadSignature, SignatureExpired):
            return False
    return False


@app.route("/api/exam/tabs")
@exam_api_required
def get_exam_tabs():
    data = load_exam_data()
    result = [
        {"id": t["id"], "name": t["name"], "card_count": len(t["cards"])}
        for t in data["tabs"]
        if t.get("id") in EXAM_PASSWORDS
    ]
    response = jsonify({"data": result})
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route("/api/exam/verify", methods=["POST"])
@exam_api_required
def verify_exam_password():
    data = request.json or {}
    tab_id = data.get("tab_id", "").strip()
    password = data.get("password", "").strip()

    tab = get_exam_tab(tab_id)
    if not tab:
        return jsonify({"ok": False, "error": "Học phần không tồn tại"}), 404
    if password != EXAM_PASSWORDS[tab_id]:
        return jsonify({"ok": False, "error": "Mật khẩu không đúng"}), 403

    # Lưu vào session — đã xác thực tab này (dùng cho web)
    session[f"exam_auth_{tab_id}"] = True
    # Đồng thời phát token ký để client mobile (không có session cookie) dùng
    exam_token = _issue_exam_token(get_api_user(), tab_id)
    return jsonify({"ok": True, "exam_token": exam_token})

@app.route("/api/exam/tabs/<tab_id>/cards")
@exam_api_required
def get_exam_tab_cards(tab_id):
    # Chặn nếu chưa xác thực password
    if not _has_exam_access(tab_id):
        return jsonify({"error": "Unauthorized"}), 401

    tab = get_exam_tab(tab_id)
    if not tab:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"tab_id": tab_id, "name": tab["name"], "cards": tab["cards"]})


@app.route("/api/exam/tabs/<tab_id>/review-progress")
@exam_api_required
def get_exam_review_progress(tab_id):
    if not _has_exam_access(tab_id):
        return jsonify({"error": "Unauthorized"}), 401
    tab = get_exam_tab(tab_id)
    if not tab:
        return jsonify({"error": "Not found"}), 404
    statuses = ExamReviewStatus.query.filter_by(
        tab_id=tab_id, user_id=get_api_user()
    ).all()
    return jsonify({"tab_id": tab_id, "statuses": [status.to_dict() for status in statuses]})


@app.route("/api/exam/tabs/<tab_id>/review-progress", methods=["PUT"])
@exam_api_required
def update_exam_review_progress(tab_id):
    if not _has_exam_access(tab_id):
        return jsonify({"error": "Unauthorized"}), 401
    tab = get_exam_tab(tab_id)
    if not tab:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}
    card_id = str(data.get("card_id", "")).strip()
    status = data.get("status", "review")
    valid_ids = {str(card.get("id")) for card in tab["cards"]}
    if card_id not in valid_ids or status not in {"mastered", "review"}:
        return jsonify({"error": "Dữ liệu ôn tập không hợp lệ"}), 400

    user_id = get_api_user()
    item = ExamReviewStatus.query.filter_by(
        tab_id=tab_id, card_id=card_id, user_id=user_id
    ).first()
    if item is None:
        item = ExamReviewStatus(tab_id=tab_id, card_id=card_id, user_id=user_id)
        db.session.add(item)
    item.status = status
    db.session.commit()
    return jsonify({"ok": True, "status": item.to_dict()})


@app.route("/api/exam/submit", methods=["POST"])
@exam_api_required
def submit_exam():
    """
    Nhận kết quả sau khi user nộp bài kiểm tra.
    Body JSON:
      {
        "tab_id"   : "kh4_6",
        "score"    : 0.85,          // tỉ lệ câu đúng 0.0–1.0
        "time_sec" : 47.3,          // thời gian hoàn thành (giây)
        "used_hint": false          // đã dùng gợi ý hay chưa
      }
    """
    user = get_api_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data      = request.get_json(silent=True) or {}
    tab_id    = data.get("tab_id", "")
    score     = float(data.get("score", 0))
    time_sec  = float(data.get("time_sec", 9999))
    used_hint = bool(data.get("used_hint", False))
    wrong_card_ids = data.get("wrong_card_ids", [])

    if not tab_id:
        return jsonify({"error": "tab_id is required"}), 400

    tab = get_exam_tab(tab_id)
    if not tab:
        return jsonify({"error": "Not found"}), 404

    valid_ids = {str(card.get("id")) for card in tab["cards"]}
    wrong_ids = {str(card_id) for card_id in wrong_card_ids if str(card_id) in valid_ids}
    for card_id in wrong_ids:
        item = ExamReviewStatus.query.filter_by(
            tab_id=tab_id, card_id=card_id, user_id=user
        ).first()
        if item is None:
            item = ExamReviewStatus(
                tab_id=tab_id, card_id=card_id, user_id=user, status="review", wrong_count=0
            )
            db.session.add(item)
        item.status = "review"
        item.wrong_count += 1
    if wrong_ids:
        db.session.commit()

    return jsonify({
        "ok": True,
        "score": score,
    })


if __name__ == "__main__":
    print("🕊️  Khởi động ứng dụng Học Khải Huyền...")
    port = int(os.environ.get("PORT", 5000))
    print(f"📖  Mở trình duyệt tại: http://localhost:{port}")
    socketio.run(app, debug=False, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)