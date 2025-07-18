# pull official base image
FROM python:3.10-slim

# set work directory
WORKDIR /usr/src/psk

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy and install dependencies, upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# copy project
COPY . .

RUN chmod +x ./gunicorn_starter.sh

RUN apt-get update && apt-get install -y dos2unix \
    && chmod +x ./gunicorn_starter.sh \
    && dos2unix ./gunicorn_starter.sh

# add abbuser
RUN adduser --disabled-password --no-create-home appuser

# workdir rights
RUN chown -R appuser:appuser /usr/src/psk

USER appuser

# set entrypoint
ENTRYPOINT ["./gunicorn_starter.sh"]