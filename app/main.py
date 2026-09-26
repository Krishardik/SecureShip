from fastapi import FastAPI

app = FastAPI(title="SecureShip")

@app.get("/")
def root():
	return  {"message":"SecureShip is running"}
