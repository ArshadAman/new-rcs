FROM nginx:alpine

# Install openssl for certificate generation
RUN apk add --no-cache openssl

# Copy the startup script to the entrypoint.d directory
# Scripts here are executed by nginx's entrypoint before starting
COPY start.sh /docker-entrypoint.d/00-generate-dummy-cert.sh
RUN chmod +x /docker-entrypoint.d/00-generate-dummy-cert.sh
