FROM python@sha256:3b05edefacf62260bc0c572aa7cb871c87052e04661d2538b1b57672a87d8041

RUN apt update
RUN apt install gettext -y

EXPOSE 8080

RUN mkdir -p /home/app
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME


WORKDIR $APP_HOME
COPY . $APP_HOME

RUN pip3 install --no-cache -r $APP_HOME/requirements.txt &&\
    pip3 install gunicorn

CMD ["gunicorn", "-c", "gunicorn_config.py", "-b", "0.0.0.0:8080", "broadcaster:app"]
