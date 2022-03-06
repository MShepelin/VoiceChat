#!/usr/bin/python3

import socket
import threading
import audioop
import time
import numpy as np
from communication import AUDIO_CHUNK, ROOM_ID_SIZE, SILENCE_RMS, DELTA_TIME


class ClientAudioReceiver:
    def __init__(self, room_id, sock, addr, on_remove):
        self.room_id = room_id
        self.sock = sock
        self.audio_buffer = threading.Lock()
        self.batches = []
        self.on_remove = on_remove
        self.addr = addr
        self.last_time = time.time()

    def send_and_check(self, data):
        try:
            self.sock.sendall(data)
        except:
            self.sock.close()

    def add_to_buffer(self, batch):
        with self.audio_buffer:
            self.batches.append(np.frombuffer(batch, dtype='int16'))

    def process_audio(self):
        while True:
            with self.audio_buffer:
                if len(self.batches) > 0:
                    data = np.array(self.batches, dtype='int16').mean(axis=0, dtype='int16') # np.frombuffer(batch, dtype='int16').tobytes()
                    threading.Thread(target=self.send_and_check, args=(data,)).start()
                    self.batches = []

    def run(self):
        threading.Thread(target=self.process_audio, args=()).start()


class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.room_lock = threading.Lock()
        self.clients = {}

    def add_client(self, sock, addr):
        with self.room_lock:
            self.clients[addr] = ClientAudioReceiver(self.room_id, sock, addr, self.remove_client)
            self.clients[addr].run()
            threading.Thread(target=self.handle_client, args=(sock, addr)).start()

    def remove_client(self, addr):
        with self.room_lock:
            self.clients.pop(addr)

    def broadcast(self, addr, data):
        with self.room_lock:
            for client_addr, client in self.clients.items():
                if client_addr != addr:
                    client.add_to_buffer(data)

    def handle_client(self, sock, addr):
        while 1:
            try:
                data = sock.recv(AUDIO_CHUNK)
                # audioop.rms(data, 2) ? SILENCE_RMS
                self.broadcast(addr, data)
            except socket.error:
                # connection closed
                sock.close()


class Server:
    def __init__(self):
        self.addr_to_room = {}
        self.print_lock = threading.Lock()
        self.room_lock = threading.Lock()

        self.ip = socket.gethostbyname(socket.gethostname())
        while 1:
            try:
                self.port = int(input('Enter port number to run on --> '))
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.bind((self.ip, self.port))
                break
            except:
                print("Couldn't bind to that port")

        self.accept_connections()

    def accept_connections(self):
        self.s.listen(100)
    
        print('Running on IP: '+self.ip)
        print('Running on port: '+str(self.port))
        
        while True:
            c, addr = self.s.accept()
            threading.Thread(target=self.handle_client,args=(c,addr)).start()

    def remove_client(self, addr, room_id):
        with self.room_lock:
            self.addr_to_room[room_id].pop(addr)
            if not self.addr_to_room[room_id]:
                self.addr_to_room.pop(room_id)

    def handle_client(self,c,addr):
        room_id = c.recv(ROOM_ID_SIZE)
        with self.print_lock:
            print("Got user with room_id", room_id)
        with self.room_lock:
            if room_id not in self.addr_to_room:
                self.addr_to_room[room_id] = Room(room_id)
            self.addr_to_room[room_id].add_client(c, addr)


server = Server()
