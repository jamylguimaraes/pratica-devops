
Repositório: https://github.com/jamylguimaraes/pratica-devops/Questao-2/

#### Implementação entregue: **Questao 2 — Monitoramento ViaIPE – Coleta e Visualização de Métrica**

---

## Sumário

1. Visão Geral
2. Arquitetura (HLD)
3. Fluxo de Funcionamento
4. Componentes do Sistema
5. Docker Compose
6. Execução do Projeto
7. Prints
8. Melhorias Futuras


---

# Monitoramento ViaIPE – Coleta e Visualização de Métricas

## 1. Visão Geral

Este projeto realiza a coleta de métricas operacionais de clientes da API ViaIPE (RNP) e armazena os dados em um banco de séries temporais (InfluxDB 1.x). As métricas coletadas são exibidas em dashboards no Grafana para auxiliar no monitoramento de disponibilidade, latência, tráfego e qualidade de conexão dos clientes.

Toda a solução é orquestrada por Docker Compose, seguindo boas práticas de separação de responsabilidades e execução em containers dedicados.


## 2. Arquitetura (HLD)

![HDL](https://github.com/jamylguimaraes/pratica-devops/blob/main/Questao-2/doc/screenshots/HLD.png)

### Componentes:

* **ViaIPE API**
  Serviço público que fornece informações de tráfego, latência, perdas e métricas de saúde dos clientes.

* **Collector (Python)**
  Aplicação responsável por consumir a API, normalizar os dados e enviar as métricas ao InfluxDB.

* **InfluxDB 1.x**
  Banco de séries temporais que armazena todas as métricas coletadas.

* **Grafana**
  Plataforma de visualização utilizada para montar dashboards operacionais.


## 3. Fluxo de Funcionamento

1. O Collector faz requisições periódicas à API ViaIPE.
2. As métricas de cada cliente são analisadas e convertidas para o formato aceito pelo InfluxDB.
3. Os dados são enviados para o InfluxDB organizados por:

   * Tags (identificação do cliente)
   * Campos (métricas numéricas)
4. O Grafana lê as séries temporais e exibe dashboards operacionais em tempo real.

## 4. Componentes do Sistema

### **Collector (Python)**

Responsável por:

* Consumir a API ViaIPE.
* Extrair métricas de latência, perdas, tráfego e disponibilidade.
* Preparar o payload de envio ao InfluxDB.
* Enviar os pontos de medição para a base.

O código completo está em: `collector/collector.py`

### **InfluxDB 1.x**

Armazena:

* Latência atual, média e máxima
* Perda de pacotes
* Tráfego de entrada e saída
* Métricas máximas e médias
* Disponibilidade estimada
* Identificação e geolocalização dos clientes

É exposto na porta **8086**.

### **Grafana**

Visualiza:

* Total de clientes monitorados
* Latência média e variação
* Perdas de pacotes
* Tráfego in/out
* Métricas agregadas por cliente

Provisionamento automático de:

* Datasource `Influx-ViaIPE`
* Dashboard com os principais gráficos


## 5. Docker Compose

O `docker-compose.yml` sobe automaticamente:

* Container do **InfluxDB**
* Container do **Grafana**
* Container do **Collector**

A rede é interna entre os serviços para segurança e isolamento.


## 6. Execução do Projeto

1. Clone o repositório localmente:

```bash
git clone https://github.com/jamylguimaraes/pratica-devops
cd pratica-devops/Questao-2/
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

5. O dashboard está disponível em: `Dashboard > Collections DashBoard.`

## 7. Prints 

Anexei capturas de telas locais em  `docs/screenshots/` 


## 8. Melhorias Futuras

* Alerts no Grafana para latência e perdas críticas
* Implementar logs estruturados no collector
* Adicionar retentativas e tolerância a falhas
* Suporte a múltiplas regiões da API ViaIPE


