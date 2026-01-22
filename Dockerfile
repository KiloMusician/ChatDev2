FROM python:3.9-slim

WORKDIR /app

# Install system deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
	python3-tk x11-apps ca-certificates && \
	rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements first to leverage caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only application source; rely on ChatDev/.dockerignore to omit large files
COPY . /app

# Do not bake secrets into the image; set at runtime (do not declare ENV here)

EXPOSE 8000

ENTRYPOINT ["/bin/bash"]