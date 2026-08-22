from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wechat-lite-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# 在线用户 {sid: {'nickname': str, 'room': str}}
users = {}
# 消息历史 {room: deque([{'nickname': str, 'msg': str, 'time': str}, ...])}
message_history = {}
MAX_HISTORY = 100

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    nickname = data.get('nickname', '匿名用户').strip()[:20]
    room = data.get('room', '大厅').strip()[:20]
    if not nickname:
        nickname = '匿名用户'
    users[request.sid] = {'nickname': nickname, 'room': room}
    join_room(room)
    
    # 初始化房间历史
    if room not in message_history:
        message_history[room] = deque(maxlen=MAX_HISTORY)
    
    # 发送历史消息给新用户
    history = list(message_history[room])
    emit('history', {'messages': history})
    
    # 广播用户加入
    now = time.strftime('%H:%M')
    emit('system', {'msg': f'{nickname} 加入了 {room}', 'time': now}, room=room)
    
    # 更新在线列表
    update_user_list(room)

@socketio.on('send_message')
def handle_message(data):
    if request.sid not in users:
        return
    user = users[request.sid]
    msg = str(data.get('msg', '')).strip()[:500]
    if not msg:
        return
    now = time.strftime('%H:%M')
    message_data = {'nickname': user['nickname'], 'msg': msg, 'time': now}
    
    # 存历史
    if user['room'] not in message_history:
        message_history[user['room']] = deque(maxlen=MAX_HISTORY)
    message_history[user['room']].append(message_data)
    
    # 广播给房间所有人
    emit('new_message', message_data, room=user['room'])

@socketio.on('switch_room')
def handle_switch_room(data):
    if request.sid not in users:
        return
    user = users[request.sid]
    old_room = user['room']
    new_room = str(data.get('room', '大厅')).strip()[:20]
    if not new_room or new_room == old_room:
        return
    
    leave_room(old_room)
    now = time.strftime('%H:%M')
    emit('system', {'msg': f'{user["nickname"]} 离开了', 'time': now}, room=old_room)
    update_user_list(old_room)
    
    user['room'] = new_room
    join_room(new_room)
    
    if new_room not in message_history:
        message_history[new_room] = deque(maxlen=MAX_HISTORY)
    
    history = list(message_history[new_room])
    emit('history', {'messages': history})
    emit('system', {'msg': f'{user["nickname"]} 加入了 {new_room}', 'time': now}, room=new_room)
    update_user_list(new_room)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid not in users:
        return
    user = users[request.sid]
    room = user['room']
    now = time.strftime('%H:%M')
    emit('system', {'msg': f'{user["nickname"]} 离开了', 'time': now}, room=room)
    del users[request.sid]
    update_user_list(room)

def update_user_list(room):
    online_users = [u['nickname'] for u in users.values() if u['room'] == room]
    emit('user_list', {'users': online_users, 'count': len(online_users)}, room=room)

if __name__ == '__main__':
    port = int(__import__('os').environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
