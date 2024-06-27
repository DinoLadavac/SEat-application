FROM python:3.10-slim-buster

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 50505

ENTRYPOINT ["gunicorn", "app:app"]