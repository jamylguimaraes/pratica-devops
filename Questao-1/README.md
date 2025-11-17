
Repositório: https://github.com/jamylguimaraes/pratica-devops/Questao-1/

#### Implementação entregue: **Questao 1 — Agente de monitoramento web**

---

## Sumário

1. Objetivo
2. High Level Design (HLD)
3. Componentes e tecnologias usadas
4. Como executar (passo a passo)
5. Agent 
6. Banco de dados
7. Grafana 
8. Prints 
9. Observações e próximos passos

---

## 1. Objetivo

Criar um agente (aplicação containerizada) que realize testes de rede para destinos (ping: latência e perda; HTTP: tempo de carregamento e códigos de retorno) para os sites:

* google.com
* youtube.com
* rnp.br

Persistir os resultados em um banco de séries temporais e expor dashboards no Grafana. A stack é orquestrada via `docker-compose` e cada componente roda em um container dedicado.

> Implementação: agente Python que grava em **InfluxDB**. Grafana para visualização.

---

## 2. High Level Design (HLD)

Arquitetura (alto nível):

```
+---------+      +-----------+      +---------+
| Agent   | ---> | InfluxDB  | <--- | Grafana |
| (Python)|      | (TS DB)   |      | (UI)    |
+---------+      +-----------+      +---------+
     |                ^
     |                |
     +--(internet)--->|
        ping / http
```

* **Agent**: container Python que executa periodicamente (agendado internamente por loop) testes ICMP (ping) e HTTP (GET) para cada target e escreve pontos no InfluxDB usando a linha de protocolo HTTP (`/write` endpoint).
* **InfluxDB**: banco de séries temporais para armazenar métricas (rtt, packet_loss, http_status, load_time_ms). Usamos InfluxDB 1.8 (compatível com linha de protocolo v1) para simplicidade.
* **Grafana**: conecta ao InfluxDB e exibe dashboards já providos (arquivo `.json` incluído) para análise de latência, perda, disponibilidade e tempos de carregamento.

---

## 3. Componentes e tecnologias usadas

* Python 3.11 (agent)
* requests (HTTP), subprocess (ping)
* InfluxDB 1.8 (image oficial)
* Grafana (image oficial)
* Docker / Docker Compose

InfluxDB é adequado para séries temporais e tem integração direta com Grafana. Python facilita executar pings e medições HTTP simples e customizadas.

---

## 4. Como executar (passo a passo)

1. Clone o repositório localmente:

```bash
git clone https://github.com/jamylguimaraes/pratica-devops
cd pratica-devops/Questao-1/
```

2. Inicie a construção com o Docker Compose:

```bash
docker-compose build --no-cache
```

3. Execute a inicialização(UP) do ambiente:

```bash
docker-compose up
```

4. Acesse Grafana: `http://localhost:3000` (user: `admin`, pass: `admin` — altere se desejar)

5. A dashboard está disponível em: `Dashboard > Web Monitor.`

6. O agent roda automaticamente a cada 60s por default; veja logs:

```bash
docker-compose logs -f agent
```

## 5. Agent 

**Funcionamento**:

* Lista de targets definida em `agent.py`.
* Para cada target:

  * Executa `ping -c 4 <host>` (no Linux) e interpreta RTT (avg) e perda de pacotes.
  * Faz `requests.get(url, timeout=15)` e mede `response.elapsed.total_seconds()` e `response.status_code`.
  * Escreve 1 ponto por verificação no InfluxDB usando a API HTTP `/write?db=monitoring` no formato Line Protocol.
* Loop infinito com `sleep(interval_seconds)`.

> Observação: o container do agent executa o utilitário `ping` disponível na imagem base (debian/ubuntu). 

## 6. Banco de dados e esquema

* Banco: **InfluxDB**
* Database: `monitoring` 
* Measurement: `web_monitor`
* Tags: `agent`, `target`, `host`
* Fields: `rtt_ms` (float), `packet_loss_pct` (float), `http_status` (integer), `load_time_ms` (integer)

## 7. Grafana — Dashboards e queries

* Dashboard provisionado automaticamente.
* Painéis em Web Monitor:

  * Latência média por target (gráfico time series)
  * Perda de pacotes (%) (gauge / time series)
  * Tempo de carregamento HTTP (histograma / time series)
  * Disponibilidade (percentual de HTTP 200 — painel singlestat)

**Datasource**: InfluxDB (influxdb:8086, database `monitoring`).

## 8. Prints 

Anexei capturas de telas locais em  `docs/screenshots/` 

## 9. Observações e próximos passos

* **Melhorias Futuras**:

  * Tornar o agente assíncrono e paralelo (asyncio) para reduzir tempo entre alvos.
  * Adicionar retries, backoff e tratamento de erros mais robusto.
  * Usar `icmplib` para ping sem depender do binário `ping`
  * Adicionar autenticação no InfluxDB / token (InfluxDB) para produção.
  



