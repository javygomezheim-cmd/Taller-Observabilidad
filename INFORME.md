# Practica Final Integradora - Stack de Observabilidad Completo

**Taller Observabilidad Infraestructura con Stack Open Source - Universidad Andres Bello**
**Integrantes:** Cristóbal Magnata Veragua, Javier Gómez Heim, Marcos Contreras Cortés y Tomás Contreras Hammad  **Fecha:** 7 de noviembre de 2026  **Repositorio:** https://github.com/javygomezheim-cmd/Taller-Observabilidad

Todo el stack usa unicamente lo visto en los talleres de clases: Prometheus, Node Exporter, snmp_exporter con un agente net-snmp (`router_sim`), Loki, Promtail, Grafana, OpenTelemetry Collector, Jaeger y HotROD. Los dashboards y la alerta se arman desde la interfaz de Grafana, como en clases.

## 1. Paso a paso documentado

### 1.1 Levantar el entorno
Con Docker Desktop en ejecucion (`docker version` debe mostrar Client y Server):
```powershell
docker compose up -d --build
docker compose ps
```
La primera vez compila net-snmp (varios minutos). 📸 `capturas/01-compose-ps.png`

URLs: Prometheus http://localhost:9090 · Grafana http://localhost:3000 (admin/admin) · Jaeger http://localhost:16686 · HotROD http://localhost:8080

### 1.2 Bloque 1 - Metricas (Prometheus, Node Exporter, SNMP)
1. En http://localhost:9090/targets deben estar **UP** `node-exporter`, `snmp_router` y `prometheus`. 📸 `capturas/02-targets.png`
2. Consulta de **uso de CPU (%)**:
   ```promql
   100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
   ```
   📸 `capturas/03-promql-cpu.png`
3. Consulta de **ancho de banda en Mbps** de la interfaz de red del agente SNMP:
   ```promql
   rate(ifHCInOctets{ifDescr="eth0"}[5m]) * 8 / 1000000
   ```
   Primero ejecuta `ifHCInOctets` para ver las etiquetas reales; si la interfaz no se llama `eth0`, ajusta el filtro. 📸 `capturas/04-promql-mbps.png`
4. Para que el trafico sea visible (por defecto solo hay el de las consultas SNMP), genera trafico hacia el agente desde un contenedor existente:
   ```powershell
   docker network ls   # buscar la red que termina en _snmp-net (depende del nombre de la carpeta del proyecto)
   docker run -d --rm --name trafico --network <proyecto>_snmp-net alpine ping -s 60000 172.21.0.12
   ```
   Por ejemplo, si la carpeta se llama `Taller-Observabilidad-pruebas`, la red es `taller-observabilidad-pruebas_snmp-net`. Para detenerlo: `docker stop trafico`. Como la consulta usa una ventana de 5 minutos (`[5m]`), el gráfico tarda unos 5 minutos en reflejar el tráfico.

### 1.3 Bloque 2 - Logs (Loki + Promtail)
1. Promtail lee `/var/log/*log` (job `varlogs`) y `cloud-logs/*.json` (job `aws_cloudtrail_sim`). Para el segundo aplica un pipeline JSON que extrae `severity` como etiqueta **`level`** y `eventName` como `action` (ver `promtail-config.yml`).
2. Para simular nuevos eventos en la nube, agrega lineas al archivo:
   ```powershell
   Add-Content .\cloud-logs\eventos.json '{"severity":"ERROR","eventName":"AccessDenied","user":"alice"}'
   Add-Content .\cloud-logs\eventos.json '{"severity":"INFO","eventName":"GetObject","user":"devops"}'
   Add-Content .\cloud-logs\eventos.json '{"severity":"WARNING","eventName":"ConsoleLoginFailed","user":"admin"}'
   ```
3. En Grafana -> Explore -> Loki, comprobar que existe la etiqueta `level` y consultar `{job="aws_cloudtrail_sim", level="ERROR"}`. 📸 `capturas/05-loki-level.png`

### 1.4 Bloque 3 - Grafana: datasources, dashboard y alerta
1. **Data sources** (Connections -> Data sources -> Add data source):
   - Prometheus: URL `http://prometheus:9090`
   - Loki: URL `http://loki:3100`
   Pulsar *Save & test* en cada uno. 📸 `capturas/06-datasources.png`
2. **Dashboard Operativo** (Dashboards -> New dashboard) con estos paneles:

   | Panel | Datasource | Visualizacion | Consulta |
   |---|---|---|---|
   | Ancho de banda (Mbps) | Prometheus | Time series | `rate(ifHCInOctets{ifDescr="eth0"}[5m]) * 8 / 1000000` |
   | Uso de CPU (%) | Prometheus | Time series | la consulta de CPU del punto 1.2 |
   | Estado del storage (% usado) | Prometheus | Gauge | `max by (device) (100 - node_filesystem_avail_bytes{fstype!~"tmpfs\|overlay\|squashfs"} / node_filesystem_size_bytes{fstype!~"tmpfs\|overlay\|squashfs"} * 100)` |
   | Logs en tiempo real | Loki | Logs | `{job="aws_cloudtrail_sim"}` |

   La consulta de storage no filtra por `mountpoint="/"` porque, dentro del contenedor, node-exporter excluye el sistema de archivos *overlay* raíz y esa serie no existe (el panel mostraba "No data"); en su lugar se toman los sistemas de archivos reales (ext4) excluyendo `tmpfs`, `overlay` y `squashfs`, y `max by (device)` evita series duplicadas del mismo disco.

   Activa el refresco automatico (5 s) y guarda como **Dashboard Operativo**. El dashboard exportado está en `grafana/dashboard-operativo.json` (Dashboards -> New -> Import). 📸 `capturas/07-dashboard-operativo.png`
3. **Alerta de CPU** (Alerting -> Alert rules -> New alert rule):
   - Consulta A (Prometheus): `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)`
   - Condicion: umbral mayor a 80 (para la demostracion puedes bajarlo temporalmente, por ejemplo a 5)
   - Evaluar cada 1 minuto, *pending period* 1 minuto
   - Contact point de tipo **Webhook** con la URL de un receptor de pruebas (por ejemplo una URL generada en https://webhook.site)
   La regla, el contact point y la política de notificación están exportados en `grafana/alerta-cpu.yaml`.

   Para subir la CPU durante la prueba se levantan dos contenedores que ejecutan un bucle infinito:
   ```powershell
   docker run -d --rm --name carga1 alpine sh -c "while true; do :; done"
   docker run -d --rm --name carga2 alpine sh -c "while true; do :; done"
   ```
   Se detienen con `docker stop carga1 carga2`. 📸 `capturas/08-alerta-firing.png` y `capturas/09-webhook-recibido.png`

### 1.5 Bloque 4 - Trazas (OpenTelemetry Collector + Jaeger + HotROD)
1. Abrir http://localhost:8080 y pulsar varios clientes para pedir viajes (cada clic genera una traza).
2. HotROD envia OTLP/HTTP a `otel-collector:4318`, que reenvia a Jaeger por OTLP gRPC (`otel-collector-config.yaml`).
3. En http://localhost:16686 elegir el servicio `frontend` -> *Find Traces*. 📸 `capturas/10-jaeger-lista.png`
4. Abrir una traza `/dispatch` y analizar el diagrama de Gantt. 📸 `capturas/11-jaeger-traza.png`

## 2. Justificacion tecnica
- **CPU**: `node_cpu_seconds_total` es un contador por nucleo y modo; `rate()` lo convierte en tasa, y medir el modo *idle* y restarlo de 100 evita sumar cada modo. `avg` consolida los nucleos.
- **Mbps**: se usa `ifHCInOctets` (64 bits) porque los contadores de 32 bits se desbordan rapido; el factor `* 8` pasa bytes a bits y `/ 1000000` a megabits.
- **snmp_exporter y `relabel_configs`**: el dispositivo objetivo viaja como parametro `target`, `instance` conserva el nombre real del agente y el scrape se redirige al exporter. Asi un solo exporter sirve para muchos equipos. El modulo `if_mib` es el estandar de interfaces de red.
- **Etiqueta `level`**: Loki indexa etiquetas y no el contenido; `level` tiene pocos valores distintos (baja cardinalidad), por lo que filtrar por severidad es rápido. `action` (el `eventName`) es más variable en un CloudTrail real: aquí son pocos eventos, pero a escala convendría dejarlo como filtro de consulta en vez de etiqueta. Los demás campos del JSON (como `user`) no se indexan.
- **Dos jobs en Promtail**: uno para los logs del sistema operativo y otro para los logs de cloud con pipeline JSON.
- **Filtros LogQL**:
  - `{job="aws_cloudtrail_sim", level="CRITICAL"}` filtra por etiquetas indexadas, que es la forma más rápida; muestra solo los eventos críticos (por ejemplo `DeleteBucket`).
  - `count_over_time({job="aws_cloudtrail_sim", level="ERROR"}[5m])` convierte logs en una métrica (errores en 5 minutos), útil para un panel o una alerta.
  - `{job="aws_cloudtrail_sim"} | json | user="admin"` filtra por un campo que no es etiqueta: el JSON se interpreta al consultar, sin aumentar la cardinalidad del índice.
- **Reglas de enrutamiento**: en Prometheus, los `relabel_configs` del job SNMP envían cada consulta al `snmp_exporter` conservando el equipo objetivo. En el Collector, el pipeline `traces` define la ruta completa: receptor OTLP HTTP (4318) → procesador `batch` → exportador OTLP gRPC hacia Jaeger (4317).
- **Gauge de storage**: se muestra el porcentaje usado, comparable entre discos de distinto tamano.
- **Alerta**: el umbral y el periodo *pending* evitan falsos positivos por picos breves; el Webhook simula la notificacion a una herramienta externa.
- **OTel Collector entre la app y Jaeger**: desacopla la aplicacion del backend de trazas; HotROD solo conoce el endpoint OTLP y el Collector decide el destino. HotROD incluye latencias deliberadas que permiten buscar cuellos de botella.

## 3. Evidencia de funcionamiento
![Dashboard operativo](capturas/07-dashboard-operativo.png)
![Alerta en Firing](capturas/08-alerta-firing.png)
![Webhook recibido](capturas/09-webhook-recibido.png)
![Webhook recibido - Evidencia adicional](capturas/09.5-webhook-recibido.png)

**Umbral usado en la demostración de la alerta:** 5 % de CPU (valor que disparó la alerta: 8,55 %, visible en `values.A` del payload recibido en el webhook). En un entorno real el umbral sería mayor, por ejemplo 80 %.

![Lista de trazas](capturas/10-jaeger-lista.png)
![Detalle de una traza](capturas/11-jaeger-traza.png)

**Análisis de una transacción** (traza `frontend: GET /dispatch`: 745 ms en total, 40 spans, 6 servicios):

| Span | Servicio | Duración | % de la traza |
|---|---|---|---|
| `GET /dispatch` | frontend | 745 ms | 100 % |
| `GET /customer` (incluye el `SQL SELECT` en mysql) | customer | 319 ms | ~43 % |
| `driver.DriverService/FindNearest` | driver | 226 ms | ~30 % |
| 10 llamadas `GET /route` | route | 32–72 ms c/u | ~27 % (en conjunto, ~200 ms) |

**Hallazgo:** la latencia se concentra en dos pasos seguidos: la consulta del cliente en MySQL (319 ms) y la búsqueda de conductores con Redis (226 ms), que juntos suman cerca del 73 % de la petición. Además, las llamadas a `route` no salen todas a la vez sino escalonadas, lo que sugiere concurrencia limitada, y en `redis-manual` aparecen 2 o 3 errores por traza (columna *Errors* de la lista), que probablemente se reintentan y suman tiempo. Se podría optimizar revisando o cacheando la consulta del cliente, investigando los errores de Redis y aumentando la concurrencia en las llamadas a `route`.

## 4. Conclusiones y lecciones aprendidas
- Las métricas dicen **qué** pasa, los logs **por qué** y las trazas **dónde**. En la traza de `/dispatch` vimos que la mayor parte del tiempo se iba en MySQL y Redis, algo que ni la CPU ni el tráfico de red mostraban por sí solos. Grafana permite ver los tres juntos.
- Una alerta de CPU con webhook avisa antes de que un usuario reporte el problema: en la demostración la regla pasó a *Firing* y el webhook recibió el aviso.
- Las etiquetas deben ser de baja cardinalidad: indexamos `level` y no `user`, para que Loki siga siendo rápido.
- Los contadores solo tienen sentido con `rate()`; sin él el valor solo crece.
- El Collector de OpenTelemetry desacopla la aplicación del backend de trazas: HotROD solo conoce un endpoint OTLP.
- Docker Compose permite levantar el entorno completo con un comando y repetirlo en otro equipo.
- **Dificultades encontradas:**
  - El panel de storage mostró "No data": node-exporter dentro de un contenedor ve el sistema de archivos *overlay* del propio contenedor, que excluye por defecto, y no el disco real. Se resolvió consultando `node_filesystem_*` sin filtrar por `mountpoint="/"` y excluyendo los tipos `tmpfs`, `overlay` y `squashfs`, con lo que aparece el disco real (ext4).
  - En Docker Desktop con WSL2, node-exporter mide la máquina virtual Linux y no Windows, por lo que la CPU y el disco que ve el dashboard corresponden a esa máquina virtual y pueden diferir del Administrador de tareas.
  - Al agregar eventos a `cloud-logs/eventos.json` desde Windows con `Add-Content`, el archivo estaba bloqueado porque Promtail lo mantiene abierto (bind mount). Se resolvió deteniendo Promtail (`docker compose stop promtail`), agregando las líneas y volviéndolo a iniciar (`docker compose start promtail`).
  - El gráfico de ancho de banda usa una ventana de 5 minutos, por lo que tarda varios minutos en reflejar el tráfico generado; además, si el equipo se suspende, Prometheus no recolecta datos y los gráficos muestran un hueco.
- **Mejoras posibles:** Alertmanager, provisioning de Grafana por archivos, retencion de logs, correlacion logs-trazas.