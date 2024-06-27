FROM python:3.10-slim-buster

WORKDIR app

COPY * /app/

RUN pip install -r requirements.txt

EXPOSE 4000

CMD ["sh", "-c", "sleep 5 && python app.py"]