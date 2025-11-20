#!/usr/bin/env python3
import os
import requests
import time
from influxdb import InfluxDBClient # type: ignore
import logging

API_URL = os.environ.get("VIAIPE_API_URL", "https://legadoviaipe.rnp.br/api/norte")
SLEEP_SECONDS = int(os.environ.get("COLLECT_INTERVAL", "60"))

INFLUX_HOST = "influxdb-viaipe"
INFLUX_PORT = 8086
INFLUX_DB = "viaipe"
INFLUX_USER = "admin"
INFLUX_PASS = "admin"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [INFO] %(message)s"
)

# -----------------------------------------
# Conectar ao InfluxDB 1.x
# -----------------------------------------
def connect_influx():
    try:
        client = InfluxDBClient(
            host=INFLUX_HOST,
            port=INFLUX_PORT,
            username=INFLUX_USER,
            password=INFLUX_PASS
        )
        databases = client.get_list_database()
        if not any(db['name'] == INFLUX_DB for db in databases):
            client.create_database(INFLUX_DB)
        client.switch_database(INFLUX_DB)
        logging.info("Conectado ao InfluxDB (1.x).")
        return client
    except Exception as e:
        logging.error(f"Erro ao conectar ao InfluxDB: {e}")
        return None
 

# -----------------------------------------
# Coleta da API ViaIPE
# -----------------------------------------
def coletar_viaipe():
    try:
        resp = requests.get(API_URL, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logging.error(f"Erro ao consultar API ViaIPE: {e}")
        return None

# -----------------------------------------
# Processar e inserir no InfluxDB
# -----------------------------------------
def processar_e_inserir(client, dados):

    registros = []

    for item in dados:

        client_id = item.get("id")
        client_name = item.get("name")

        lat = float(item.get("lat"))
        lng = float(item.get("lng"))

        smoke = item.get("data", {}).get("smoke", {})
        interfaces = item.get("data", {}).get("interfaces", [])

        # ----- Smoke metrics -----
        loss = smoke.get("loss", 0)
        avg_loss = smoke.get("avg_loss", 0)
        max_loss = smoke.get("max_loss", 0)
        val = smoke.get("val", 0)               # latência instantânea
        avg_val = smoke.get("avg_val", 0)       # latência média
        max_val = smoke.get("max_val", 0)       # latência pico

        # Disponibilidade baseada na perda de pacotes
        availability = 100 - (loss * 100)

        # ----- Interface metrics (somatória das interfaces) -----
        traffic_in = sum(i.get("traffic_in", 0) for i in interfaces)
        traffic_out = sum(i.get("traffic_out", 0) for i in interfaces)
        avg_in = sum(i.get("avg_in", 0) for i in interfaces)
        avg_out = sum(i.get("avg_out", 0) for i in interfaces)
        max_in = sum(i.get("max_in", 0) for i in interfaces)
        max_out = sum(i.get("max_out", 0) for i in interfaces)
        max_traffic_up = sum(i.get("max_traffic_up", 0) for i in interfaces)
        max_traffic_down = sum(i.get("max_traffic_down", 0) for i in interfaces)

        # client_side é bool → transformar em int
        client_side = sum(1 if i.get("client_side") else 0 for i in interfaces)

        # last interface name (pode ser lista também)
        interface_names = ",".join(i.get("nome", "unknown") for i in interfaces)
        interface_types = ",".join(i.get("tipo", "unknown") for i in interfaces)
        graph_ids = ",".join(i.get("traffic_graph_id", "") for i in interfaces)

        ponto = {
            "measurement": "viaipe_metrics",
            "tags": {
                "client_id": client_id,
                "client_name": client_name,
                "interface_names": interface_names,
                "interface_types": interface_types,
                "graph_ids": graph_ids
            },
            "fields": {
                "lat": float(lat),
                "lng": float(lng),

                # Smoke
                "loss": float(loss),
                "avg_loss": float(avg_loss),
                "max_loss": float(max_loss),
                "latency": float(val),
                "latency_avg": float(avg_val),
                "latency_max": float(max_val),

                # Interfaces
                "traffic_in": float(traffic_in),
                "traffic_out": float(traffic_out),
                "avg_in": float(avg_in),
                "avg_out": float(avg_out),
                "max_in": float(max_in),
                "max_out": float(max_out),
                "max_traffic_up": float(max_traffic_up),
                "max_traffic_down": float(max_traffic_down),
                "client_side_count": int(client_side),

                # Disponibilidade
                "availability": float(availability)
            }
        }

        registros.append(ponto)

    if registros:
        client.write_points(registros)
        logging.info(f"{len(registros)} pontos enviados ao InfluxDB.")


# -----------------------------------------
# Loop principal
# -----------------------------------------
def main():
    client = connect_influx()

    while True:
        dados = coletar_viaipe()
        if dados:
            if client is not None:
                processar_e_inserir(client, dados)
            else:
                logging.warning("Não foi possível conectar ao InfluxDB. Tentando novamente em 10 segundos...")
                time.sleep(10)
                client = connect_influx()
        else:
            logging.warning("Não foram encontrados dados na API ViaIPE. Tentando novamente em 10 segundos...")
            time.sleep(10)
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main()
