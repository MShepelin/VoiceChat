#!/usr/bin/python3

import socket
import threading
import pyaudio
import queue
import audioop
# audioop.rms(data, 2) ? SILENCE_RMS
from communication import AUDIO_CHUNK, ROOM_ID_SIZE, NAME_SIZE


class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.name = bytes(input('Enter your name --> '), encoding='utf-8')
        self.room_id = bytes(input('Enter your room id --> '), encoding='utf-8')[:ROOM_ID_SIZE]
        self.room_id = self.room_id.rjust(ROOM_ID_SIZE, b'0')
        while 1:
            try:
                self.target_ip = input('Enter IP address of server --> ')
                self.target_port = int(input('Enter target port of server --> '))
                self.s.connect((self.target_ip, self.target_port))
                break
            except:
                print("Couldn't connect to server")

        chunk_size = AUDIO_CHUNK
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 4000

        # initialise microphone recording
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True, frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
        
        print("Connected to Server")

        try:
            self.s.send(self.room_id)
            self.s.send(self.name[:NAME_SIZE])
            threading.Thread(target=self.receive_server_data).start()
            self.send_data_to_server()
        except Exception as e:
            print('Unexpected error occurred', e)

    def receive_server_data(self):
        while True:
            try:
                data = self.s.recv(AUDIO_CHUNK)
                self.playing_stream.write(data)
            except:
                pass

    def send_data_to_server(self):
        while True:
            try:
                data = self.recording_stream.read(AUDIO_CHUNK)
                self.s.sendall(data)
            except socket.error as e:
                self.s.close()
                print('Session ended', flush=True)
                break


client = Client()
