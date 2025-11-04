# Use a lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Default runtime envs
ENV PORT=5000 \
    WORKERS=4 \
    THREADS=2

# Set work directory
WORKDIR /app

# Install Python dependencies first (better cache usage)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the app port
EXPOSE 5000

# Start the app with gunicorn
CMD ["sh", "-c", "gunicorn -w ${WORKERS} -k gthread --threads ${THREADS} -b 0.0.0.0:${PORT} app:app"]
