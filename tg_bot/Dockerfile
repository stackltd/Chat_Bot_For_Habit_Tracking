# FROM python:latest
#
# RUN mkdir app
#
# COPY . app/
#
# WORKDIR app/
#
# RUN python -m pip install --upgrade pip
#
# RUN python -m pip install -r requirements.txt
#
# CMD python bot.py


FROM python:3.12-slim

RUN mkdir app
RUN mkdir app/tg_bot
WORKDIR app/

COPY requirements.txt ./tg_bot

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ./tg_bot/requirements.txt

COPY . ./tg_bot

CMD python -m tg_bot.bot