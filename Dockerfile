# Use an official Python runtime as the base image
FROM python:3.12.4-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the project code into the container
COPY . /app/

# Copy the wait-for-it script and make it executable
COPY wait-for-db.sh /app/wait-for-db.sh
RUN chmod +x /app/wait-for-db.sh

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Make the entrypoint script the default command
ENTRYPOINT ["/app/entrypoint.sh"]

# Create a non-root user and switch to it
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# The entrypoint script will be executed in docker-compose
CMD ["gunicorn", "-c", "gunicorn.conf.py", "resume_analyzer.wsgi:application"]


