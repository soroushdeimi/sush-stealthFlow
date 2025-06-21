# StealthFlow Server Dockerfile
# Docker image for StealthFlow server

FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    supervisor \
    tzdata \
    locales \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configure locale
RUN locale-gen en_US.UTF-8

# Create xray user
RUN useradd -r -s /usr/sbin/nologin xray

# Create necessary directories
RUN mkdir -p /etc/xray /var/log/xray /var/log/nginx /var/www/html

# Install Xray-core
RUN XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4) && \    wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" && \
    unzip Xray-linux-64.zip && \
    mv xray /usr/local/bin/ && \
    chmod +x /usr/local/bin/xray && \
    rm -f Xray-linux-64.zip

# Copy configuration files
COPY server/configs/xray-config.json /etc/xray/config.json.template
COPY server/nginx/nginx.conf /etc/nginx/nginx.conf.template
COPY server/scripts/docker-entrypoint.sh /docker-entrypoint.sh
COPY server/scripts/generate-config.sh /usr/local/bin/generate-config.sh
COPY server/scripts/health-server.py /usr/local/bin/health-server.py

# Set permissions
RUN chmod +x /docker-entrypoint.sh /usr/local/bin/generate-config.sh /usr/local/bin/health-server.py && \
    chown -R xray:xray /etc/xray /var/log/xray

# Configure Supervisor
COPY server/configs/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create simple web page
RUN echo '<html><body><h1>Welcome to nginx!</h1><p>Server is running.</p></body></html>' > /var/www/html/index.html

# Expose ports
EXPOSE 80 443

# Configure volumes
VOLUME ["/etc/xray", "/var/log", "/etc/letsencrypt"]

# Configure health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Entry point
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
