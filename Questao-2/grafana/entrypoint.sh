#!/bin/bash

echo "Copiando arquivos de provisionamento..."

mkdir -p /etc/grafana/provisioning/datasources
mkdir -p /etc/grafana/provisioning/dashboards

cp -r /etc/grafana/setup/postgres.yaml /etc/grafana/provisioning/datasources/
cp -r /etc/grafana/setup/dashboard.yaml /etc/grafana/provisioning/dashboards/
cp -r /etc/grafana/setup/metricas-dashboard.json /etc/grafana/provisioning/dashboards/

echo "Iniciando Grafana..."
/run.sh