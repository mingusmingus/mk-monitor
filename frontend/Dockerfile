## Frontend Dockerfile (Vite + React)
## Build con Node y servir con Nginx

FROM node:20-alpine AS build
WORKDIR /app

# Instalar dependencias
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund

# Copiar el resto del código fuente
COPY frontend/ .

# Construir artefactos de producción
RUN npm run build

# Imagen de producción (Nginx)
FROM nginx:alpine AS prod

# Copiar configuración personalizada de Nginx (SPA fallback)
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copiar artefactos construidos
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
