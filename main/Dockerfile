FROM python:3.10-slim-buster

WORKDIR app

COPY * /app/

RUN pip install -r requirements.txt

EXPOSE 4000

CMD python app.py