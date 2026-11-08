# Stack de observabilidad con Docker Compose

Práctica final integradora — Taller Observabilidad Infraestructura con Stack Open Source (Universidad Andrés Bello).

Stack open source que cubre los tres pilares de la observabilidad:

- **Métricas:** Prometheus, Node Exporter y snmp_exporter (con un agente SNMP simulado, `router_sim`).
- **Logs:** Loki y Promtail (con pipeline JSON que indexa la etiqueta `level`).
- **Trazas:** OpenTelemetry Collector, Jaeger y HotROD (aplicación de microservicios de prueba).
- **Visualización y alertas:** Grafana.

El detalle completo (paso a paso, justificación técnica, evidencias y conclusiones) está en [INFORME.md](INFORME.md).

## Requisitos

- Docker Desktop en ejecución (`docker version` debe mostrar *Client* y *Server*).
- Puertos libres: 3000, 3100, 4317, 4318, 8080, 9090, 9100, 9116, 16686 y 161/udp.
- Si quedó levantado algún taller anterior que use la red `172.21.0.0/24`, bajarlo antes con `docker compose down`.

## Cómo levantarlo

```powershell
docker compose up -d --build
docker compose ps
```

La primera vez compila net-snmp para `router_sim`, lo que demora varios minutos. Para detener todo: `docker compose down`.

## Servicios

| Servicio | URL | Notas |
|---|---|---|
| Prometheus | http://localhost:9090 | Estado de los targets en `/targets` |
| Grafana | http://localhost:3000 | Usuario `admin`, contraseña `admin` |
| Jaeger | http://localhost:16686 | Servicio `frontend` para ver las trazas |
| HotROD | http://localhost:8080 | Cada clic genera una traza |
| Loki | http://localhost:3100 | Se consulta desde Grafana (Explore) |
| Node Exporter | http://localhost:9100/metrics | Métricas del sistema |
| snmp_exporter | http://localhost:9116 | Consulta el agente `router_sim` |

En Grafana hay que agregar dos data sources: Prometheus (`http://prometheus:9090`) y Loki (`http://loki:3100`).

## Archivos del repositorio

| Archivo | Para qué sirve |
|---|---|
| `docker-compose.yml` | Define todos los servicios y la red `snmp-net` |
| `prometheus.yml` | Targets de Prometheus (Node Exporter y SNMP vía snmp_exporter) |
| `promtail-config.yml` | Lectura de logs del sistema y de los logs cloud simulados, con pipeline JSON |
| `otel-collector-config.yaml` | Pipeline de trazas: receptor OTLP HTTP → batch → Jaeger |
| `Dockerfile` y `snmpd.conf` | Imagen y configuración del agente SNMP simulado |
| `cloud-logs/eventos.json` | Log simulado de eventos cloud (severidad, evento, usuario) |
| `grafana/dashboard-operativo.json` | Dashboard Operativo exportado (importar en Grafana: Dashboards → New → Import) |
| `grafana/alerta-cpu.yaml` | Regla "Alerta CPU", contact point webhook y política de notificación |
| `capturas/` | Capturas que respaldan el informe |
| `INFORME.md` | Informe técnico |
