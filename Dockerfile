FROM python:3.12-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first
COPY server/pyproject.toml server/pyproject.toml
COPY server/README.md server/README.md

WORKDIR /app/server

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install .

# Copy application code
COPY server /app/server

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "src.metakb.main:app", "--host", "0.0.0.0", "--port", "8000"]
