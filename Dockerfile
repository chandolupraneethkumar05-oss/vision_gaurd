# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime Python Container
FROM python:3.11-slim
WORKDIR /app

# System dependencies for OpenCV & image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source & frontend built artifacts
COPY src/ src/
COPY scripts/ scripts/
COPY docs/ docs/
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# Install visionguard package
RUN pip install --no-cache-dir -e .

EXPOSE 8000

ENV VG_HOST=0.0.0.0
ENV VG_PORT=8000

CMD ["uvicorn", "visionguard.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
