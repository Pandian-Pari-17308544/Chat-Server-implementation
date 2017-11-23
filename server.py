from hashlib import md5
import socket
import sys
import threading
import collections
import Queue

class Multi_Thread_Handler(threading.Thread):
    def __init__(self, inbound_conn):
        threading.Thread.__init__(self)
        self.inbound_conn = inbound_conn

    def run(self):
        while True:
            socket, address = self.inbound_conn.get()
            single_connection_handler(socket, address)
            self.inbound_conn.task_done()

def boradcast_message(room_id, data):
    for chatroom_join_id, connection in rooms[room_id].iteritems():
        connection.sendall(data)

def single_connection_handler(socket, address):
    while True:
        data = socket.recv(2048).decode('utf-8')
        
        if data.startswith("HELO"):
            socket.sendall("{0}\nIP:{1}\nPORT:{2}\nStudentID:{3}".format(data.strip(), "134.226.32.10", str(address[1]), "12326755"))
            continue
        
        elif data.startswith("KILL_SERVICE"):
            socket.close()
            break
        
        data = data.split('\n')
        action_key_val = data[0]
        action_name = action_key_val[:action_key_val.find(':')]
        
        if (action_name == 'CHAT'):
            room_id = int(data[0].split(":")[1])
            chatroom_join_id = int(data[1].split(":")[1])
            client_name = data[2].split(":")[1]
            boradcast_message(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), data[3].split(":")[1]))
        elif (action_name == 'JOIN_CHATROOM'):
            client_name = data[3].split(":")[1]
            room_name = data[0].split(":")[1]
            room_id = int(md5(room_name).hexdigest(), 16)
            chatroom_join_id = int(md5(client_name).hexdigest(), 16)
            if room_id not in rooms:
                rooms[room_id] = dict()
            if chatroom_join_id not in rooms[room_id]:
                rooms[room_id][chatroom_join_id] = socket
                socket.sendall("JOINED_CHATROOM:{0}\nSERVER_IP:{1}\nPORT:{2}\nROOM_REF:{3}\nJOIN_ID:{4}\n".format(str(room_name), address[0], address[1], str(room_id), str(chatroom_join_id)))
                boradcast_message(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}".format(str(room_id), str(client_name), str(client_name) + " has joined this chatroom.\n\n"))

        elif (action_name == 'LEAVE_CHATROOM'):
            room_id = int(data[0].split(":")[1])
            chatroom_join_id = int(data[1].split(":")[1])
            client_name = data[2].split(":")[1]
            socket.sendall("LEFT_CHATROOM:{0}\nJOIN_ID:{1}\n".format(str(room_id), str(chatroom_join_id)))
            boradcast_message(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), str(client_name) + " has left this chatroom."))
            del rooms[room_id][chatroom_join_id]

        elif (action_name == 'DISCONNECT'):
            client_name = data[2].split(":")[1]
            chatroom_join_id = int(md5(client_name).hexdigest(), 16)
            for room_id in rooms.keys():
                if chatroom_join_id in rooms[room_id]:
                    boradcast_message(room_id, "CHAT:{0}\nCLIENT_NAME:{1}\nMESSAGE:{2}\n\n".format(str(room_id), str(client_name), str(client_name) + " has left this chatroom."))
                    if chatroom_join_id in rooms[room_id]:
                        del rooms[room_id][chatroom_join_id]
            break


rooms = collections.OrderedDict()
inbound_conn = Queue.Queue(maxsize=100)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = socket.gethostbyname(socket.gethostname())
sock.bind((ip, int(sys.argv[1])))
sock.listen(5)

while True:
    connection, address = sock.accept()
    conn_handler = Multi_Thread_Handler(inbound_conn)
    conn_handler.setDaemon(True)
    conn_handler.start()
    inbound_conn.put((connection, address))
