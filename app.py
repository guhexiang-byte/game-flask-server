from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os
import time

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False
DB_FILE = "forum_data.db"
MAX_MESSAGE_COUNT = 80

# 初始化数据库表
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT,
        create_time REAL,
        content TEXT
    )
    ''')
    conn.commit()
    conn.close()

# 数据库工具函数
def db_query(sql, args=()):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(sql, args)
    res = cur.fetchall()
    conn.close()
    return res

def db_execute(sql, args=()):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return """
===持久化论坛接口===
GET  /api/forum?room=房间名 → 获取留言列表
POST /api/forum?room=房间名 → 发布留言
DELETE /api/forum?room=房间名 → 清空房间全部留言
DELETE /api/forum?room=房间名&index=数字 → 删除指定单条
"""

@app.route('/api/forum', methods=["GET", "POST", "DELETE"])
def forum():
    try:
        room_id = request.args.get("room", "default").strip()

        if request.method == "POST":
            json_data = request.get_json()
            now = time.time()
            db_execute(
                "INSERT INTO messages(room, create_time, content) VALUES (?,?,?)",
                (room_id, now, str(json_data))
            )
            # 超出上限，删除最早消息
            all_msg = db_query("SELECT id FROM messages WHERE room=? ORDER BY create_time ASC", (room_id,))
            if len(all_msg) > MAX_MESSAGE_COUNT:
                remove_count = len(all_msg) - MAX_MESSAGE_COUNT
                for i in range(remove_count):
                    mid = all_msg[i][0]
                    db_execute("DELETE FROM messages WHERE id=?", (mid,))

        elif request.method == "DELETE":
            index_text = request.args.get("index")
            if index_text is None:
                db_execute("DELETE FROM messages WHERE room=?", (room_id,))
            else:
                idx = int(index_text)
                data = db_query("SELECT id FROM messages WHERE room=? ORDER BY create_time ASC", (room_id,))
                if 0 <= idx < len(data):
                    mid = data[idx][0]
                    db_execute("DELETE FROM messages WHERE id=?", (mid,))

        # 查询当前房间所有消息
        rows = db_query("SELECT create_time, content FROM messages WHERE room=? ORDER BY create_time ASC", (room_id,))
        output = []
        for t, c in rows:
            output.append({"time": t, "content": eval(c)})
        return jsonify(output)

    except Exception as e:
        return jsonify({"code": -1, "msg": "请求异常"}), 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
