# pull official base image
FROM python:3.10-slim

# set work directory
WORKDIR /usr/src/psk

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy and install dependencies, upgrade pip
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \

# copy project
COPY . .

# Создаем непривилегированного пользователя
RUN adduser --disabled-password --no-create-home appuser

# Даем права на рабочую директорию
RUN chown -R appuser:appuser /usr/src/psk

USER appuser

# set entrypoint
ENTRYPOINT ["./gunicorn_starter.sh"]