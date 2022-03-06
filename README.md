# Voice Chat

В этом репозитории приложен код для сервера и клиента голосового чата с поддержкой нескольких комнат, общением 2 и более пользователей одновременно, а также отправкой сообщения, только при условии достаточной громкости говорящего.

### How to

**Запуск сервера** можно осуществить через docker, а также через локальный запуск питоновского файла. При запуске контейнера docker не забудьте сделать expose выбранного порта.

```bash
> docker pull mityashepelin/voice-chat
> docker run -p 8080:8080 mityashepelin/voice-chat
Enter port number to run on --> 808
Couldn't bind to that port
Enter port number to run on --> 8081
Running on IP: 172.23.144.1
Running on port: 8081
Got user b'e' with room_id b'000000000000000e'
Got user b'e' with room_id b'000000000000000e'
Connection with ('172.23.144.1', 56659) finished
Connection with ('172.23.144.1', 56653) finished
```

**Запуск клиента** осуществляется через питоновский файл, который можно при необходимости кастомизировать. Базовый клиент реализует не отправляет запись микрофона, если пользователь "молчит" (то есть средняя громкость посчитанная по rms не достигает достаточного значения).

### Описание решения

Одной из задач было создание **логики для заглушки клиента**, которую было решено реализовать на стороне клиента.

```python
data = self.recording_stream.read(AUDIO_CHUNK)
rms = audioop.rms(data, 2)

if data_queue.qsize() > 0:
	data_queue.put(rms, block=False)
	cur_rms += rms

	if data_queue.qsize() < SLIDING_MEAN:
		self.s.sendall(data)
	else:
		cur_rms -= data_queue.get(block=False)
	if cur_rms / data_queue.qsize() < SILENCE_RMS:
		data_queue = queue.Queue()
	else:
		self.s.sendall(data)

elif rms > ACTIVATION_RMS:
	data_queue.put(rms, block=False)
	cur_rms += rms
	self.s.sendall(data)
```

Задача общения **2 и более пользователей** решается гораздо сложнее. Так как производительность python не позволяет написать быстрый процессинг, то пришлось наладить баланс между частотой записи/воспроизведения, а также размером батча аудиоданных, чтобы объединять батчи разных источников с помощью среднего.

```python
while not self.sock._closed:
    with self.audio_buffer:
        if len(self.batches) > 0:
            data = np.array(self.batches, dtype='int16').mean(axis=0, dtype='int16')
            threading.Thread(target=self.send_and_check, args=(data,)).start()
            self.batches = []
```

Задача **обеспечения нескольких комнат и актуализации списка пользователей** решается с помощью mutex-локов для синхронизации потоков, системы классов, которая разделяет ответственность запуска процессинга, а также протокола перевода данных о коде комнаты и ника пользователя.

```python
try:
    room_id = c.recv(ROOM_ID_SIZE)
    user_name = c.recv(NAME_SIZE)
except:
    with print_lock:
        print("User initialisation failed")
    return

with print_lock:
    print("Got user", user_name, "with room_id", room_id)
```

### Альтернативы

В ходе решения были изучены альтернативы для создания голосового чата. В частности, стоит отметить решение через WebRTC, которая позволяет создать peer-to-peer соединение между клиентами, что упрощает объединение аудио с нескольких источников. Можно также запускать эти соединения с помощью нескольких аудио-каналов.



