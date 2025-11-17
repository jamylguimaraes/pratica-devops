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

def run_ping(host, count=4, timeout=10):
    """Return (avg_rtt_ms (float) or None, packet_loss_pct (float) or None)"""
    try:
        proc = subprocess.run(["ping", "-c", str(count), host],
                              capture_output=True, text=True, timeout=timeout)
        out = proc.stdout
        loss = None
        rtt = None
        # packet loss: look for 'X% packet loss' pattern
        m = re.search(r"(\d+(?:\.\d+)?)% packet loss", out)
        if m:
            loss = float(m.group(1))
        # rtt line: rtt min/avg/max/mdev = 13.123/13.456/13.789/0.123 ms
        m2 = re.search(r"rtt .* = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)", out)
        if m2:
            try:
                rtt = float(m2.group(2))  # avg in ms
            except:
                rtt = None
        return rtt, loss
    except Exception:
        return None, None

def run_http(url, timeout=15):
    """Return (status_code int or None, load_time_ms int or None)"""
    try:
        r = requests.get(url, timeout=timeout)
        elapsed_ms = int(r.elapsed.total_seconds() * 1000)
        return r.status_code, elapsed_ms
    except Exception:
        return None, None

def line_protocol(measurement, tags, fields, timestamp=None):
    """
    Build InfluxDB line protocol string.
    Integers must be suffixed with i. Strings quoted.
    """
    tagset = ",".join([f"{k}={v}" for k, v in tags.items()])
    fpairs = []
    for k, v in fields.items():
        if isinstance(v, int):
            fpairs.append(f"{k}={v}i")
        elif isinstance(v, float):
            # ensure float has decimal
            fpairs.append(f"{k}={v}")
        elif isinstance(v, str):
            fpairs.append(f'{k}="{v}"')
        else:
            # fallback to string
            fpairs.append(f'{k}="{v}"')
    fieldset = ",".join(fpairs)
    if tagset:
        line = f"{measurement},{tagset} {fieldset}"
    else:
        line = f"{measurement} {fieldset}"
    if timestamp:
        line = f"{line} {timestamp}"
    return line

def write_influx(line):
    try:
        requests.post(INFLUX_URL, data=line, timeout=5)
    except Exception as e:
        # Errors but print for debugging
        print(f"[WARN] failed write to influx: {e}")

def wait_startup():
    # small startup wait so influx can bind
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