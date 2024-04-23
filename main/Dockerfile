FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

EXPOSE 4000

CMD ["sh", "-c", "sleep 5 && python app.py"]