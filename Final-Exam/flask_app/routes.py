# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
from flask import current_app as app
from flask import jsonify
from flask import render_template, redirect, request, session, url_for, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from .utils.database.database  import database
from werkzeug.datastructures   import ImmutableMultiDict
from pprint import pprint
import json
import random
import functools
from . import socketio
db = database()


#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function

def getUser():
	return db.reversibleEncrypt('decrypt', session['email']) if 'email' in session else 'Unknown'

@app.route('/login')
def login():
	return render_template('login.html', user=getUser())

@app.route('/logout')
def logout():
	session.pop('email', default=None)
	return redirect('/')

@app.route('/processlogin', methods=["POST", "GET"])
def processlogin():
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    check = db.authenticate(form_fields['email'], form_fields['password'])
    if check['success'] == 1:
        response = {'success': 1}
        session['email'] = db.reversibleEncrypt('encrypt', form_fields['email'])
        return json.dumps(response)
    else:
        response = {'success': 0}
        return json.dumps(response)
        

#######################################################################################
# SIGNUP RELATED
#######################################################################################

@app.route('/signup')
def signup():
     return render_template('signup.html', user=getUser())

@app.route('/processSignup', methods=["POST", "GET"])
def processSignup():
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    print('##############################################')
    check = db.half_authenticate(form_fields['email'])
    if check['success'] == 1:
        response = {'success': 0}
        return json.dumps(response)
    else:
        db.createUser(form_fields['email'], form_fields['password'], role='user')
        response = {'success': 1}
        return json.dumps(response)

#######################################################################################
# CHATROOM RELATED
#######################################################################################
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=getUser())

@socketio.on('joined', namespace='/chat')
def joined(message):
    print('here')
    join_room('main')
    if getUser() == 'owner@email.com':
        emit('status', {'msg': getUser() + ' has entered the room.', 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
        emit('status', {'msg': getUser() + ' has entered the room.', 'style': 'width: 100%;color:grey;text-align: left'}, room='main')

@socketio.on('left', namespace="/chat")
def left(message):
    if getUser() == 'owner@email.com':
        emit('status', {'msg': getUser() + 'has left the chat.', 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
        emit('status', {'msg': getUser() + 'has left the chat.', 'style': 'width: 100%;color:grey;text-align: left'}, room='main')
    leave_room('main')

@socketio.on('text_message', namespace='/chat')
def text(message):
    if getUser() == 'owner@email.com':
        emit('status', {'msg': message['msg'], 'style': 'width: 100%;color:blue;text-align: right'}, room='main')
    else:
         emit('status', {'msg': message['msg'], 'style': 'width: 100%;color:grey;text-align: left'}, room='main')
     
#######################################################################################
# NEW BOARD RELATED
#######################################################################################
@app.route('/new_board')
@login_required
def new_board():
    return render_template('new_board.html', user=getUser())

@app.route('/processboard', methods=["POST", "GET"])
def processboard():
    form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
    name = form_fields.get('name')
    members = form_fields.get('members').split(', ')
    members[0] = getUser()
    check = db.createBoard(name, members)
    return json.dumps(check)
#######################################################################################
# NEW BOARD RELATED
#######################################################################################
@app.route('/existing_board')
@login_required
def existing_board():
    all_data = db.existing_data(getUser())
    return render_template('existing_board.html', user=getUser(), all_data=all_data)


#######################################################################################
# INDIVIDUAL BOARD RELATED
#######################################################################################

@app.route('/board/<int:board_id>')
@login_required
def display_board(board_id):
    board_data = db.getBoardData(board_id)
    task_data = db.getTaskData(board_id)
    tasks_length = len(task_data)
    return render_template('board.html', board_data=board_data, user=getUser(), task_data=task_data, tasks_length=tasks_length)

@socketio.on('joined', namespace='/board')
def handle_joined(message):
    join_room(message['board_id'])
    emit('status', {'msg': 'Connected to board room: ' + message['board_id']}, room=message['board_id'])

@app.route('/processtask', methods=["POST", "GET"])
def processtask():
     form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
     board_id = form_fields.get('board_id')

     if form_fields.get('process') == 'edit':
            task_id = form_fields.get('task_id')
            description = form_fields.get('description')
            check = db.editTask(task_id, description)
            socketio.emit('update_page', {'process':'edit', 'task_id': task_id, 'description': description}, room=board_id)

     elif form_fields.get('process') == 'add':
            board_id = form_fields.get('board_id')
            description = form_fields.get('description')
            category = form_fields.get('category')
            task_id = db.createTask(board_id, description, category)
            socketio.emit('update_page', {'process':'add', 'board_id': board_id, 'description': description, 'category': category}, room=board_id)
            return json.dumps({'success': 1, 'task_id': task_id})

     elif form_fields.get('process') == 'move':
            task_id = form_fields.get('task_id')
            category = form_fields.get('category')
            check = db.moveTask(task_id, category)
            socketio.emit('update_page', {'process':'move', 'task_id': task_id, 'category': category}, room=board_id)

     elif form_fields.get('process') == 'delete':
            task_id = form_fields.get('task_id')
            print(db.deleteTask(task_id))
            socketio.emit('update_page', {'process':'delete', 'task_id': task_id}, room=board_id)

     return json.dumps({'success':1})

@socketio.on('connect', namespace='/board/<int:board_id>')
def board_connect(board_id):
     session['board_id'] = board_id
     print(f'Client connected to /board/{board_id} namespace')
@socketio.on('disconnect', namespace='/board/<int:board_id>')
def board_disconnect(board_id):
     print(f'Client disconnected from /board/{board_id} namespace')
#######################################################################################
# OTHER
#######################################################################################
@app.route('/')
def root():
	return redirect('/signup')

@app.route('/home')
@login_required
def home():
	x = random.choice(['I started university when I was a wee lad of 15 years.','I have a pet sparrow.','I write poetry.'])
	return render_template('home.html', user=getUser(), fun_fact = x)

@app.route('/board_type')
@login_required
def board_type():
     return render_template('board_type.html', user=getUser())

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r
