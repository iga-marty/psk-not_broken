# pull official base image
FROM python:3.6.3-slim

# set work directory
WORKDIR /usr/src/psk

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY requirements.txt /usr/src/psk/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/psk/

# set entrypoint
ENTRYPOINT ["./gunicorn_starter.sh"]