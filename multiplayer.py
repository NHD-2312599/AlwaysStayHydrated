# -*- coding: utf-8 -*-
"""
Multiplayer quiz (kiểu Kahoot/Quiz.com) dùng bộ câu hỏi Khải Huyền.

- Chủ phòng tạo phòng -> nhận mã 6 chữ số ngẫu nhiên.
- Người chơi nhập mã để vào phòng (chờ ở sảnh).
- Chủ phòng bấm Bắt đầu -> lần lượt hiển thị câu hỏi trắc nghiệm
  (được sinh tự động từ verse + hàm make_blank_question có sẵn).
- Điểm mỗi câu = điểm_gốc(theo độ khó) x hệ_số_tốc_độ, sai = 0 điểm.
- Toàn bộ state phòng được lưu trong bộ nhớ (dict) — đủ dùng cho 1 tiến
  trình server. Nếu sau này scale nhiều worker/instance thì cần chuyển
  sang Redis (Flask-SocketIO hỗ trợ message_queue=redis://...).
"""

import random
import re
import string
import time
import threading

from flask import request
from flask_socketio import join_room, leave_room, emit


def _normalize_answer(text):
    """Chuẩn hoá chuỗi trả lời để so sánh: bỏ khoảng trắng thừa, dấu câu, viết thường."""
    text = (text or "").strip().lower()
    text = re.sub(r'[.,;:!?"“”\'’]', "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ─── Cấu hình điểm ────────────────────────────────────────────────────────
BASE_POINTS = {1: 500, 2: 750, 3: 1000}
MIN_SPEED_FACTOR = 0.5   # trả lời sát giờ vẫn được tối thiểu 50% điểm gốc
DEFAULT_TIME_LIMIT = 20  # giây mỗi câu
DEFAULT_NUM_QUESTIONS = 10
REVEAL_DELAY = 4         # giây hiển thị đáp án trước khi tự chuyển câu tiếp

_lock = threading.Lock()
ROOMS = {}  # room_code(str) -> Room


def _gen_room_code():
    while True:
        code = "".join(random.choices(string.digits, k=6))
        if code not in ROOMS:
            return code


class Room:
    def __init__(self, code, host_sid, host_name, settings):
        self.code = code
        self.host_sid = host_sid
        self.host_name = host_name
        self.settings = settings  # {chapter, start_verse, end_verse, level, num_questions, time_limit}
        self.state = "lobby"      # lobby | playing | reveal | ended
        self.players = {host_sid: {"name": host_name, "score": 0, "streak": 0}}
        self.questions = []       # list các câu đã sinh sẵn
        self.current_index = -1
        self.question_deadline = 0
        self.answers = {}         # sid -> {"text": str, "time_taken": float, "correct": bool, "points": int}
        self.round_token = 0      # tăng mỗi lần chuyển câu, để hủy timer cũ

    def player_list(self):
        return [
            {"sid": sid, "name": p["name"], "score": p["score"], "streak": p.get("streak", 0)}
            for sid, p in sorted(self.players.items(), key=lambda kv: -kv[1]["score"])
        ]


def register_multiplayer(socketio, BIBLE_DATA, make_blank_question):
    """Gắn toàn bộ socket event handler vào app. Gọi 1 lần từ app.py."""

    def _room_of_sid(sid):
        for room in ROOMS.values():
            if sid in room.players or sid == room.host_sid:
                return room
        return None

    def _gen_question(verse_obj, chapter, level):
        """Sinh câu hỏi điền vào chỗ trống — người chơi tự gõ đáp án."""
        q_text, answer = make_blank_question(verse_obj["text"], level)
        if not answer:
            return None

        display_question = (
            q_text if level != 3
            else f"Điền đúng toàn bộ câu Khải Huyền {chapter}:{verse_obj['verse']}"
        )
        return {
            "question": display_question,
            "answer": answer,
            "chapter": chapter,
            "verse": verse_obj["verse"],
            "level": level,
        }

    def _build_questions(settings):
        chapter = settings.get("chapter", "random")
        start_verse = int(settings.get("start_verse", 1))
        end_verse = int(settings.get("end_verse", 9999))
        level = int(settings.get("level", 1))
        num_questions = max(1, min(30, int(settings.get("num_questions", DEFAULT_NUM_QUESTIONS))))

        chapters_to_try = (
            [str(random.randint(1, 22)) for _ in range(num_questions * 3)]
            if chapter == "random" else [str(int(chapter))] * (num_questions * 5)
        )

        questions = []
        seen = set()
        for ch in chapters_to_try:
            if len(questions) >= num_questions:
                break
            verses = BIBLE_DATA.get(ch, [])
            filtered = [v for v in verses if start_verse <= v["verse"] <= end_verse]
            if not filtered:
                continue
            verse_obj = random.choice(filtered)
            key = (ch, verse_obj["verse"])
            if key in seen:
                continue
            q = _gen_question(verse_obj, ch, level)
            if q:
                seen.add(key)
                questions.append(q)
        return questions

    def _clear_answer_state(room):
        room.answers = {}

    def _score_answer(room, level, time_taken, time_limit, correct):
        if not correct:
            return 0
        base = BASE_POINTS.get(level, 500)
        remaining = max(0.0, time_limit - time_taken)
        speed_factor = MIN_SPEED_FACTOR + (1 - MIN_SPEED_FACTOR) * (remaining / time_limit)
        return round(base * speed_factor)

    def _send_question(room):
        room.current_index += 1
        room.round_token += 1
        token = room.round_token

        if room.current_index >= len(room.questions):
            room.state = "ended"
            socketio.emit("mp_game_over", {"leaderboard": room.player_list()}, to=room.code)
            return

        q = room.questions[room.current_index]
        time_limit = room.settings.get("time_limit", DEFAULT_TIME_LIMIT)
        room.state = "playing"
        room.question_deadline = time.time() + time_limit
        _clear_answer_state(room)

        socketio.emit("mp_question", {
            "index": room.current_index,
            "total": len(room.questions),
            "question": q["question"],
            "time_limit": time_limit,
            "level": q["level"],
            "chapter": q["chapter"],
            "verse": q["verse"],
        }, to=room.code)

        def _timeout_watcher(code, expected_token):
            socketio.sleep(time_limit)
            with _lock:
                r = ROOMS.get(code)
                if not r or r.round_token != expected_token or r.state != "playing":
                    return
                _reveal(r)

        socketio.start_background_task(_timeout_watcher, room.code, token)

    def _reveal(room):
        with _lock:
            if room.state != "playing":
                return
            room.state = "reveal"
            q = room.questions[room.current_index]
            time_limit = room.settings.get("time_limit", DEFAULT_TIME_LIMIT)
            results = []
            for sid, p in room.players.items():
                ans = room.answers.get(sid)
                if ans:
                    results.append({
                        "name": p["name"], "answered": True,
                        "correct": ans["correct"], "points_earned": ans["points"],
                        "time_taken": round(ans["time_taken"], 2),
                        "streak": p.get("streak", 0),
                        "answer_text": ans["text"],
                    })
                else:
                    room.players[sid]["streak"] = 0  # không trả lời kịp -> đứt chuỗi
                    results.append({"name": p["name"], "answered": False, "correct": False, "points_earned": 0, "streak": 0, "answer_text": ""})
            token = room.round_token
            code = room.code
            correct_answer = q["answer"]
            leaderboard = room.player_list()

        socketio.emit("mp_question_result", {
            "correct_answer": correct_answer,
            "results": results,
            "leaderboard": leaderboard,
        }, to=code)

        def _auto_next(code, expected_token):
            socketio.sleep(REVEAL_DELAY)
            with _lock:
                r = ROOMS.get(code)
                if not r or r.round_token != expected_token or r.state != "reveal":
                    return
                _send_question(r)

        socketio.start_background_task(_auto_next, code, token)

    # ─── Socket.IO events ──────────────────────────────────────────────

    @socketio.on("mp_create_room")
    def on_create_room(data):
        sid = request.sid
        name = (data.get("username") or "Chủ phòng").strip()[:24] or "Chủ phòng"
        settings = {
            "chapter": data.get("chapter", "random"),
            "start_verse": data.get("start_verse", 1),
            "end_verse": data.get("end_verse", 9999),
            "level": int(data.get("level", 1)),
            "num_questions": int(data.get("num_questions", DEFAULT_NUM_QUESTIONS)),
            "time_limit": int(data.get("time_limit", DEFAULT_TIME_LIMIT)),
        }
        with _lock:
            code = _gen_room_code()
            room = Room(code, sid, name, settings)
            ROOMS[code] = room
        join_room(code)
        emit("mp_room_created", {"code": code, "host_name": name})

    @socketio.on("mp_join_room")
    def on_join_room(data):
        sid = request.sid
        code = str(data.get("code", "")).strip()
        name = (data.get("username") or "Người chơi").strip()[:24] or "Người chơi"

        with _lock:
            room = ROOMS.get(code)
            if not room:
                emit("mp_error", {"message": "Mã phòng không tồn tại."})
                return
            if room.state != "lobby":
                emit("mp_error", {"message": "Phòng đã bắt đầu chơi, không thể vào lúc này."})
                return
            room.players[sid] = {"name": name, "score": 0, "streak": 0}
            players = room.player_list()
            host_name = room.host_name

        join_room(code)
        emit("mp_joined", {"code": code, "host_name": host_name})
        socketio.emit("mp_players_update", {"players": players}, to=code)

    @socketio.on("mp_start_game")
    def on_start_game(data):
        sid = request.sid
        code = str(data.get("code", "")).strip()
        with _lock:
            room = ROOMS.get(code)
            if not room or room.host_sid != sid:
                emit("mp_error", {"message": "Chỉ chủ phòng mới có thể bắt đầu."})
                return
            if len(room.players) == 0:
                emit("mp_error", {"message": "Cần ít nhất 1 người chơi để bắt đầu."})
                return
            room.questions = _build_questions(room.settings)
            if not room.questions:
                emit("mp_error", {"message": "Không đủ dữ liệu câu hỏi cho lựa chọn này. Hãy chọn chương khác."})
                return
            room.current_index = -1

        socketio.emit("mp_game_started", {}, to=code)
        _send_question(room)

    @socketio.on("mp_submit_answer")
    def on_submit_answer(data):
        sid = request.sid
        code = str(data.get("code", "")).strip()
        answer_text = str(data.get("text", "") or "")[:500]

        with _lock:
            room = ROOMS.get(code)
            if not room or room.state != "playing" or sid not in room.players:
                return
            if sid in room.answers:
                return  # đã trả lời rồi
            q = room.questions[room.current_index]
            time_limit = room.settings.get("time_limit", DEFAULT_TIME_LIMIT)
            time_taken = max(0.0, time_limit - max(0.0, room.question_deadline - time.time()))
            correct = bool(answer_text.strip()) and (_normalize_answer(answer_text) == _normalize_answer(q["answer"]))
            points = _score_answer(room, q["level"], time_taken, time_limit, correct)
            room.answers[sid] = {"text": answer_text, "time_taken": time_taken, "correct": correct, "points": points}
            room.players[sid]["score"] += points
            if correct:
                room.players[sid]["streak"] = room.players[sid].get("streak", 0) + 1
            else:
                room.players[sid]["streak"] = 0
            new_streak = room.players[sid]["streak"]
            all_answered = len(room.answers) >= len(room.players)

        emit("mp_answer_ack", {"correct": correct, "points": points, "streak": new_streak})

        if all_answered:
            with _lock:
                room = ROOMS.get(code)
                should_reveal = room is not None and room.state == "playing"
            if should_reveal:
                _reveal(room)

    @socketio.on("mp_leave_room")
    def on_leave_room(data):
        _handle_disconnect(request.sid)

    @socketio.on("disconnect")
    def on_disconnect():
        _handle_disconnect(request.sid)

    def _handle_disconnect(sid):
        with _lock:
            room = _room_of_sid(sid)
            if not room:
                return
            code = room.code
            if sid == room.host_sid:
                del ROOMS[code]
                ended = True
            else:
                room.players.pop(sid, None)
                ended = False
                players = room.player_list()

        if ended:
            socketio.emit("mp_room_closed", {"message": "Chủ phòng đã rời phòng."}, to=code)
        else:
            socketio.emit("mp_players_update", {"players": players}, to=code)
