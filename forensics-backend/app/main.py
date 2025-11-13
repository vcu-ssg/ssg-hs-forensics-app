from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os
#from run_sam2 import generate_segmentation

app = FastAPI()

@app.get("/hello/*")
def root():
    return {"message": "Hello from FastAPI behind NGINX! on /api/hello"}

@app.get("/goodbye")
def root():
    return {"message": "Goodby from FastAPI behind NGINX! on /api/goodbye"}

# TODO: Feature to add in the future.
# checks if image has been processed in the past, and returns the stored processed results if it has been
#@app.get("/get-img/{img_name}")
#async def get_image(img_name: str):
    # get image file name without extension (it is used as the directory name)
    #directory_name = img_name.split(sep='.')[0]
    #if os.path.isdir(f"/usr/share/nginx/user-images/{directory_name}"):


# TODO: Hook up the SAM model to this function so it instead passes the received image to the function.
# processes a new image
UPLOAD_DIRECTORY_FASTAPI = "/images/uploaded-images"
PROCESSED_DIRECTORY_FASTAPI = "/images/processed-images"
PREVIEW_DIRECTORY_NGINX = "/images/processed-images"

@app.post("/process-img")
async def upload_image(image: UploadFile = File(...)):
    try:
        # Save the uploaded image to a local file
        contents = await image.read()
        # save original upload
        upload_path = os.path.join(UPLOAD_DIRECTORY_FASTAPI, image.filename)
        with open(upload_path, "wb") as f:
            f.write(contents)

        # TODO: call segmentation/model processing here and write real processed output
        # For now, write the processed file as a copy into the processed directory
        processed_path = os.path.join(PROCESSED_DIRECTORY_FASTAPI, f"processed_{image.filename}")
        with open(processed_path, "wb") as f:
            f.write(contents)

        # return url to processed file to client
        return JSONResponse(content={"image_url": f"{PREVIEW_DIRECTORY_NGINX}/processed_{image.filename}"})
    except Exception as e:
        return {"error": f"Failed to process image: {e}"}
    finally:
        # make sure to close the image object
        image.close()

