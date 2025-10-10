from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def root():
    return {"message": "Hello from FastAPI behind NGINX! on /api/hello"}

@app.get("/goodbye")
def root():
    return {"message": "Goodby from FastAPI behind NGINX! on /api/goodbye"}

