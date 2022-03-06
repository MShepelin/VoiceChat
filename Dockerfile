FROM python:3.7-alpine
COPY . .
RUN pip install -r requirements.txt
CMD python3 -u server-tcp.py