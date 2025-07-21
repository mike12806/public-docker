# Use a lightweight nginx base image
FROM nginx:alpine

# Copy static website content
COPY resume/ /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
