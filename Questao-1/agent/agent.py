#!/usr/bin/env python3
import time
import subprocess
import requests
import socket
import os
import re

INFLUX_URL = os.environ.get("INFLUX_URL", "http://influxdb:8086/write?db=monitoring")
INTERVAL = int(os.environ.get("INTERVAL", "60"))

TARGETS = [
    {"name": "google", "host": "google.com", "url": "https://www.google.com"},
    {"name": "youtube", "host": "youtube.com", "url": "https://www.youtube.com"},
    {"name": "rnp", "host": "rnp.br", "url": "https://www.rnp.br"},
]

# -----------------------------------------
# Executa ping e HTTP checks,
# retorna métricas rtt_ms (float), packet_loss_pct (float)
# -----------------------------------------
def run_ping(host, count=4, timeout=10):
    try:
        proc = subprocess.run(["ping", "-c", str(count), host],
                              capture_output=True, text=True, timeout=timeout)
        out = proc.stdout
        loss = None
        rtt = None
        # packet loss: look for 'X% packet loss'
        m = re.search(r"(\d+(?:\.\d+)?)% packet loss", out)
        if m:
            loss = float(m.group(1))
        m2 = re.search(r"rtt .* = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)", out)
        if m2:
            try:
                rtt = float(m2.group(2)) 
            except:
                rtt = None
        return rtt, loss
    except Exception:
        return None, None

# -----------------------------------------
# Executa http checks
# retorna status_code (int), load_time_ms (int)
# -----------------------------------------
def run_http(url, timeout=15):
    try:
        r = requests.get(url, timeout=timeout)
        elapsed_ms = int(r.elapsed.total_seconds() * 1000)
        return r.status_code, elapsed_ms
    except Exception:
        return None, None

# -----------------------------------------
# Cria linha no formato line protocol do InfluxDB
# integers devem ter sufixo i, strings entre aspas
# -----------------------------------------
def line_protocol(measurement, tags, fields, timestamp=None):
    
    tagset = ",".join([f"{k}={v}" for k, v in tags.items()])
    fpairs = []
    for k, v in fields.items():
        if isinstance(v, int):
            fpairs.append(f"{k}={v}i")
        elif isinstance(v, float):
            fpairs.append(f"{k}={v}")
        elif isinstance(v, str):
            fpairs.append(f'{k}="{v}"')
        else:
            fpairs.append(f'{k}="{v}"')
    fieldset = ",".join(fpairs)
    if tagset:
        line = f"{measurement},{tagset} {fieldset}"
    else:
        line = f"{measurement} {fieldset}"
    if timestamp:
        line = f"{line} {timestamp}"
    return line

# -----------------------------------------
# Escreve linha no InfluxDB
# -----------------------------------------
def write_influx(line):
    try:
        requests.post(INFLUX_URL, data=line, timeout=5)
    except Exception as e:
        print(f"[WARN] failed write to influx: {e}")

# -----------------------------------------
# Espera inicial para startup
# -----------------------------------------
def wait_startup():
    print("Agent starting, waiting a few seconds for services...")
    time.sleep(8)

if __name__ == "__main__":
    wait_startup()
    hostname = socket.gethostname()
    print("Agent running. Targets:", [t['host'] for t in TARGETS])
    while True:
        for t in TARGETS:
            host = t['host']
            name = t['name']
            rtt, loss = run_ping(host)
            status, load_ms = run_http(t['url'])

            tags = {"agent": hostname, "target": name, "host": host}
            fields = {}
            if rtt is not None:
                # convert to float ms
                fields['rtt_ms'] = float(rtt)
            if loss is not None:
                fields['packet_loss_pct'] = float(loss)
            if status is not None:
                fields['http_status'] = int(status)
            if load_ms is not None:
                fields['load_time_ms'] = int(load_ms)

            if fields:
                line = line_protocol("web_monitor", tags, fields)
                print(f"[INFO] write: {line}")
                write_influx(line)
            else:
                print(f"[INFO] no metrics for {host}")

        time.sleep(INTERVAL)