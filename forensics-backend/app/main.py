from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import shutil
import os
from run_sam2 import generate_segmentation

app = FastAPI()

@app.get("/hello")
def root():
    return {"message": "Hello from FastAPI behind NGINX! on /api/hello"}

@app.get("/goodbye")
def root():
    return {"message": "Goodby from FastAPI behind NGINX! on /api/goodbye"}

# TODO: Hook up the SAM model to this function so it instead passes the received image to the function.
@app.post("/img")
async def upload_image(image: UploadFile = File(...)):
    try:
        # Save the uploaded image to a local file
        temp_filename = f"uploaded_{image.filename}"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        #return {"message": f"Image '{image.filename}' uploaded successfully!"}
        return FileResponse(path=temp_filename, media_type="image/png", filename="edited_image.png")
    except Exception as e:
        return {"error": f"Failed to upload image: {e}"}

