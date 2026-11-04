# Paquete 2: Logs: Loki, Promtail, generador de log JSON

**Rama:** `feature/logs`  **Depende de:** paquete 1 ya mergeado en develop

## Archivos de este paquete
- `docker-compose.yml`
- `prometheus/prometheus.yml`
- `loki/loki-config.yml`
- `promtail/promtail-config.yml`
- `loggen/loggen.py`
- `logs/.gitkeep`

## Pasos (desde la raiz del repositorio clonado)
1. Descomprime este zip **en la raiz del repo**, aceptando reemplazar `docker-compose.yml` / `prometheus.yml` si existen.
2. Crea tu rama desde `develop` actualizado:
   ```bash
   git checkout develop && git pull origin develop
   git checkout -b feature/logs
   ```
3. Prueba lo tuyo antes de subir: `docker compose up -d --build` y revisa los servicios de tu bloque.
4. Commit y push:
   ```bash
   git add .
   git commit -m "feat(logs): agrega Loki, Promtail y generador de log JSON con etiqueta level"
   git push -u origin feature/logs
   ```
5. Abre un Pull Request hacia `develop` y pide revision a un companero. Hacer merge solo cuando este aprobado.

Captura sugerida: `05-loki-labels.png` (Explore -> Loki -> `{job="cloud-logs", level="error"}`).

> Lee y entiende cada archivo antes de subirlo: tendras que explicar tu bloque en la defensa.
