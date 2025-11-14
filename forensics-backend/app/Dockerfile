FROM python:3.11-slim

# Install OpenCV dependencies + wget for model download
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download the SAM model checkpoint
RUN wget -q https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth -O /app/sam_vit_b_01ec64.pth

COPY . .

# Create image directories
RUN mkdir -p /images/uploaded-images /images/processed-images /images/sample-gallery-images

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]