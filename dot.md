# docker build -t yourdockerhubusername/your-app-name:latest .
# docker push yourdockerhubusername/your-app-name:latest

version: '3.8'

services:
  db:
    image: postgres:13  # Specifying a fixed version for stability
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USERNAME}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  migrate:
    image: yourdockerhubusername/your-app-name:latest
    command: python manage.py migrate
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_PROVIDER=${DATABASE_PROVIDER}
      - DB_NAME=${DB_NAME}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432

  app:
    image: yourdockerhubusername/your-app-name:latest
    command: gunicorn --bind 0.0.0.0:8000 resume_analyzer.wsgi:application
    depends_on:
      - migrate
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - DATABASE_PROVIDER=${DATABASE_PROVIDER}
      - DB_NAME=${DB_NAME}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - EMAIL_PORT=${EMAIL_PORT}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_volume:/app/static
    depends_on:
      - app

volumes:
  db-data:
  static_volume:

networks:
  default:
    name: resume_analyzer_network