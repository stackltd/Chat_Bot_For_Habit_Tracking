FROM python:latest

RUN mkdir app

COPY . app/

WORKDIR app/

RUN python -m pip install --upgrade pip

RUN python -m pip install -r requirements.txt

CMD python bot.py
