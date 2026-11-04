"""Genera un log JSON simulado de un servicio en la nube (formato tipo GCP/AWS)."""
import json, random, time, uuid
from datetime import datetime, timezone

LEVELS = ["INFO"] * 6 + ["WARNING"] * 2 + ["ERROR"] * 2 + ["DEBUG"]
SERVICES = ["cloud-api", "cloud-storage", "cloud-auth"]
MESSAGES = {
    "INFO": ["solicitud procesada", "objeto subido a bucket", "token emitido"],
    "DEBUG": ["cache hit", "consulta ejecutada en 12ms"],
    "WARNING": ["latencia elevada en backend", "cuota al 85%"],
    "ERROR": ["timeout conectando a S3", "fallo de autenticacion", "error 500 en upstream"],
}

with open("/logs/cloud.log", "a", buffering=1) as f:
    while True:
        level = random.choice(LEVELS)
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "severity": level,
            "service": random.choice(SERVICES),
            "region": "sa-east-1",
            "message": random.choice(MESSAGES[level]),
            "request_id": uuid.uuid4().hex[:8],
        }) + "\n")
        time.sleep(random.uniform(0.5, 2))
