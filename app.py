from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
import time, json, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wechat-lite-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

users = {}  # sid: {'nickname': str, 'room': str}
message_history = {}  # room: deque
MAX_HISTORY = 50

@app.route('/')
def index():
    return 'TurboWarp Chat Server Running'

@socketio.on('message')
def handle_message(data):
    try:
        msg = json.loads(data) if isinstance(data, str) else data
    except:
        return
    msg_type = msg.get('type', '')
    
    if msg_type == 'join':
        nickname = str(msg.get('nickname', '匿名'))[:20]
        room = str(msg.get('room', '大厅'))[:20]
        users[request.sid] = {'nickname': nickname, 'room': room}
        join_room(room)
        if room not in message_history:
            message_history[room] = deque(maxlen=MAX_HISTORY)
        # 发历史
        for m in message_history[room]:
            emit('message', json.dumps(m))
        # 广播加入
        now = time.strftime('%H:%M')
        sys_msg = {'type': 'system', 'msg': f'{nickname} 加入了', 'time': now}
        emit('message', json.dumps(sys_msg), room=room)
        update_user_list(room)
    
    elif msg_type == 'chat':
        if request.sid not in users:
            return
        user = users[request.sid]
        content = str(msg.get('msg', ''))[:300]
        if not content:
            return
        now = time.strftime('%H:%M')
        chat_msg = {'type': 'chat', 'nickname': user['nickname'], 'msg': content, 'time': now}
        if user['room'] not in message_history:
            message_history[user['room']] = deque(maxlen=MAX_HISTORY)
        message_history[user['room']].append(chat_msg)
        emit('message', json.dumps(chat_msg), room=user['room'])
    
    elif msg_type == 'switch':
        if request.sid not in users:
            return
        user = users[request.sid]
        new_room = str(msg.get('room', '大厅'))[:20]
        old_room = user['room']
        if new_room == old_room:
            return
        leave_room(old_room)
        now = time.strftime('%H:%M')
        emit('message', json.dumps({'type': 'system', 'msg': f'{user["nickname"]} 离开了', 'time': now}), room=old_room)
        update_user_list(old_room)
        user['room'] = new_room
        join_room(new_room)
        if new_room not in message_history:
            message_history[new_room] = deque(maxlen=MAX_HISTORY)
        for m in message_history[new_room]:
            emit('message', json.dumps(m))
        emit('message', json.dumps({'type': 'system', 'msg': f'{user["nickname"]} 加入了', 'time': now}), room=new_room)
        update_user_list(new_room)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid not in users:
        return
    user = users[request.sid]
    room = user['room']
    now = time.strftime('%H:%M')
    emit('message', json.dumps({'type': 'system', 'msg': f'{user["nickname"]} 离开了', 'time': now}), room=room)
    del users[request.sid]
    update_user_list(room)

def update_user_list(room):
    online = [u['nickname'] for u in users.values() if u['room'] == room]
    list_msg = {'type': 'userlist', 'users': online, 'count': len(online)}
    emit('message', json.dumps(list_msg), room=room)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
