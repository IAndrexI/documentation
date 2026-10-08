# ==============================================================================
# Multi-Stage Build: MkDocs Material -> Minimalist Nginx Alpine (<15MB RAM)
# ==============================================================================

# Stage 1: Build static documentation
FROM squidfunk/mkdocs-material:latest AS builder
WORKDIR /docs
COPY . .
RUN mkdocs build --clean

# Stage 2: Production Nginx Server
FROM nginx:alpine
LABEL maintainer="Andrew (Protutech)"
COPY --from=builder /docs/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
