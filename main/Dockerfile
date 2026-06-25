# FROM python:latest
#
# RUN mkdir app
#
# RUN mkdir app/main
#
# COPY . app/main/
#
# WORKDIR app/
#
# RUN python -m pip install --upgrade pip
#
# RUN python -m pip install -r ./main/requirements.txt
#
# RUN chmod +x ./main/wait-for-it.sh
#
# CMD ./main/wait-for-it.sh postgres:5432 -- uvicorn main.app:app --host 0.0.0.0 --port 8088


# Используем легковесный образ (экономим ~800 МБ)
FROM python:3.11-slim

# Устанавливаем системные зависимости, необходимые для wait-for-it (netcat)
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

RUN mkdir app
RUN mkdir app/main
WORKDIR app/

COPY requirements.txt ./main

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r ./main/requirements.txt

COPY . ./main

RUN chmod +x ./main/wait-for-it.sh

CMD ./main/wait-for-it.sh postgres:5432 -- uvicorn main.app:app --host 0.0.0.0 --port 8088