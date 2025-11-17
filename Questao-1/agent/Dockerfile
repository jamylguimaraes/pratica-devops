FROM python:3.11-slim

# instalar ping e dependências
RUN apt-get update && \
    apt-get install -y --no-install-recommends iputils-ping ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .

ENV INFLUX_URL="http://influxdb:8086/write?db=monitoring"
ENV INTERVAL=60

CMD ["python", "agent.py"]