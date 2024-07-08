FROM python:3.9-slim

WORKDIR /celery

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
