FROM python:3.12-slim

# Prevent Python from buffering logs
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install system deps
# TODO: remove git dep once civicpy is updated in pypi
RUN apt-get update && \
    apt-get install -y libpq-dev gcc git \
    && rm -rf /var/lib/apt/lists/*


# Copy only dependency files first
COPY server /app/server

WORKDIR /app/server

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install .

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "src.metakb.main:app", "--host", "0.0.0.0", "--port", "8000"]
