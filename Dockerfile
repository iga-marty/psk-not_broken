# pull official base image
FROM python:3.9.7

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
RUN chmod 600 gunicorn_starter.sh
RUN chmod +x gunicorn_starter.sh
ENTRYPOINT ["./gunicorn_starter.sh"]