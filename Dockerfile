FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV AM_I_IN_A_DOCKER_CONTAINER 1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . /app
WORKDIR /app

RUN mkdir -p /app/logs
# RUN pip install -r requirements.txt

# VOLUME [ "/app/logs" ]

EXPOSE 8000

# CMD [ "python3", "main.py" ]