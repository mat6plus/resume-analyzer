user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    upstream django {
        server app:8000;
    }

    server {
        listen 80;
        server_name localhost;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/nginx.crt;
        ssl_certificate_key /etc/nginx/ssl/nginx.key;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/static/;
            expires 1d;
            add_header Cache-Control "public, max-age=86400";
        }

        location /media/ {
            alias /app/media/;
            expires 1d;
            add_header Cache-Control "public, max-age=86400";
        }
    }
}



# events {
#     worker_connections 1024;
# }

# http {
#     upstream django {
#         server app:8000;
#     }

#     server {
#         listen 80;
#         server_name localhost;
#         return 301 https://$server_name$request_uri;
#     }

#     server {
#         listen 443 ssl;
#         server_name localhost;

#         ssl_certificate /etc/nginx/ssl/nginx.crt;
#         ssl_certificate_key /etc/nginx/ssl/nginx.key;

#         location / {
#             proxy_pass http://django;
#             proxy_set_header Host $host;
#             proxy_set_header X-Real-IP $remote_addr;
#         }

#         location /static/ {
#             alias /app/static/;
#         }

#         location /media/ {
#             alias /app/media/;
#         }
#     }
# }

----

services:
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USERNAME}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - backend

  app:
    build:
      context: .
      dockerfile: Dockerfile
    command: sh -c "./wait-for-db.sh db 5432 ./entrypoint.sh"
    depends_on:
      db:
        condition: service_healthy
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=0
      - DB_NAME=${DB_NAME}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - EMAIL_PORT=${EMAIL_PORT}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    restart: unless-stopped
    networks:
      - backend
      - frontend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - frontend

volumes:
  db-data:
  static_volume:
  media_volume:

networks:
  backend:
  frontend:
# services:
#   db:
#     image: postgres:15
#     environment:
#       - POSTGRES_DB=${DB_NAME}
#       - POSTGRES_USER=${DB_USERNAME}
#       - POSTGRES_PASSWORD=${DB_PASSWORD}
#     volumes:
#       - db-data:/var/lib/postgresql/data
#     healthcheck:
#       test: ["CMD-SHELL", "pg_isready -U ${DB_USERNAME} -d ${DB_NAME}"]
#       interval: 10s
#       timeout: 5s
#       retries: 5
#     restart: unless-stopped

#   app:
#     build:
#       context: .
#       dockerfile: Dockerfile
#     command: sh -c "./wait-for-db.sh db 5432 ./entrypoint.sh"
#     depends_on:
#       db:
#         condition: service_healthy
#     environment:
#       - SECRET_KEY=${SECRET_KEY}
#       - DEBUG=0
#       - DB_NAME=${DB_NAME}
#       - DB_USERNAME=${DB_USERNAME}
#       - DB_PASSWORD=${DB_PASSWORD}
#       - DB_HOST=db
#       - DB_PORT=5432
#       - EMAIL_HOST=${EMAIL_HOST}
#       - EMAIL_HOST_USER=${EMAIL_HOST_USER}
#       - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
#       - EMAIL_PORT=${EMAIL_PORT}
#     ports:
#       - "8000:8000"
#     restart: unless-stopped

# volumes:
#   db-data:
