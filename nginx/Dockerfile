FROM nginx:alpine

# Install openssl for certificate generation
RUN apk add --no-cache openssl

# Copy the startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Use the script as entrypoint
ENTRYPOINT ["/start.sh"]

# Default command
CMD ["nginx", "-g", "daemon off;"]
