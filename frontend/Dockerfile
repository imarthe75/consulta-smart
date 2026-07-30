# Frontend Dockerfile

FROM node:26-alpine

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy rest of application
COPY . .

# Usuario no-root (hallazgo de seguridad, guía de remediación imarthe75 2026-07-29).
# node:alpine ya trae un usuario "node" (uid 1000, coincide con el uid del host que es
# dueño del bind mount ./frontend:/app). NOTA: el volumen nombrado frontend-node-modules
# puede tener contenido de ejecuciones previas escrito como root — si tras reconstruir
# la imagen aparecen errores de permisos en node_modules, recrear ese volumen
# (docker volume rm) para que el usuario "node" pueda escribirlo desde cero.
RUN chown -R node:node /app
USER node

# Expose port
EXPOSE 5173

# Development command
CMD ["npm", "run", "dev", "--", "--host"]
