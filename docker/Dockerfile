FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

ENV PYTHONUNBUFFERED=1
CMD ["bash", "-lc", "make scrape && make index && python api/main.py"]
