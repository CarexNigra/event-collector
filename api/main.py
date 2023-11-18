from fastapi import FastAPI

app = FastAPI()

@app.post("/store")
async def store_event():
    return {"message": "204 OK"}