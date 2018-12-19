from flask import Flask,request
from flask_socketio import SocketIO, send,emit
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)
clients = []
##@socketio.on('connect')
##def handleConnect():
##    print('Connect: '+request.sid)
##    clients.append(request.sid)
    
##@socketio.on('disconnect')
##def handle_disconnect():
##    print('Client disconnected')
##    clients.remove(request.sid)


@socketio.on('message')
def handle_message(msg):
    print(msg)
    socketio.send(msg,broadcard=True)

def sendCardMessage(json):
    print('Message:'+json)
    socketio.emit('messageCardFromServer', json)
    
def sendCarMessage(json):
    print('Message:'+json)
    socketio.emit('messageCarFromServer', json)
    
def run():
    app.run(host='0.0.0.0',port='8000')