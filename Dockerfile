# Use a lightweight Python image
FROM python

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Default runtime envs
ENV PORT=5000

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
CMD ["gunicorn", "-k", "gthread", "-b", "0.0.0.0:5000", "app:app"]