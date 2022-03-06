FROM python:3.6
COPY . .
RUN apt-get update
RUN apt-get install libasound-dev libportaudio2 libportaudiocpp0 portaudio19-dev -y
RUN pip install -r requirements.txt
CMD python3 -u server-tcp.py
