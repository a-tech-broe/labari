FROM node:20-alpine AS builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
# Use empty API URL so all API calls go through nginx proxy on the same origin
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/out /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
