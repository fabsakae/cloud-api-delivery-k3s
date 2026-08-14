import os
import psycopg2
from fastapi import FastAPI, HTTPException

app = FastAPI()

# O Python "pesca" a credencial injetada pelo cofre do Kubernetes
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
def health_check():
    db_status = "error"
    
    try:
        # Tenta estabelecer uma conexão real e rápida com o DBaaS
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            db_status = "ok"
        else:
            db_status = "missing_url"
    except Exception as e:
        print(f"Erro de conexão com o banco: {e}")
        db_status = "disconnected"

    # Retorna o status no formato exato exigido pela esteira de observabilidade
    if db_status == "ok":
        return {"status": "ok", "database": "ok"}
    else:
        # Se falhar, retorna Erro 503 (Serviço Indisponível)
        raise HTTPException(status_code=503, detail={"status": "error", "database": db_status})