from fastapi import FastAPI


app = FastAPI(
    title="VoltNest Customer Support",
)


@app.get("/health")
def health():
    return {"status": "ok"}