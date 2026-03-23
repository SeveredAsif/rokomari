from fastapi import FastAPI

app = FastAPI(title="Recommendation Service", version="0.2.0")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "recommendation-service"}


@app.get("/hello")
def hello_from_recommendation():
    return {
        "message": "hello from recommendation service",
        "service": "recommendation-service",
    }
