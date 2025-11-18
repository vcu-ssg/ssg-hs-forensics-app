FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# create directories for user uploaded images, which get remade each time Docker containers are created
RUN mkdir -p /app/original-user-images
RUN mkdir -p /app/processed-user-images

#RUN wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
