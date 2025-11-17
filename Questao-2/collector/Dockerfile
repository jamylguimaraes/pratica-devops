FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY collector.py /app/collector.py

ENV PYTHONUNBUFFERED=1
ENV VIAIPE_API_URL="https://legadoviaipe.rnp.br/api/norte"
ENV COLLECT_INTERVAL=60 

CMD ["python", "collector.py"]
