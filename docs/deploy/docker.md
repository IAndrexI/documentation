# Docker & Docker Compose Deployment

How to host the documentation using Docker Compose on Proxmox, Portainer, or any Linux server.

---

## 1. Using Docker Compose

Run with standard `docker compose`:

```bash
docker compose up -d
```

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  docs:
    image: squidfunk/mkdocs-material:latest
    container_name: protutech-docs
    restart: unless-stopped
    ports:
      - "8085:8000"
    volumes:
      - .:/docs
    command: serve --dev-addr=0.0.0.0:8000
```

---

## 2. Production Multi-Stage Dockerfile (Ultra-Light Nginx)

For maximum performance and sub-15MB RAM usage, build a minimal Nginx container:

```bash
docker build -t protutech-docs:latest .
docker run -d -p 8085:80 --name protutech-docs --restart unless-stopped protutech-docs:latest
```
