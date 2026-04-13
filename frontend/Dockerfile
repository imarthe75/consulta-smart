# Frontend Dockerfile

FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json ./
COPY package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy rest of application
COPY . .

# Expose port
EXPOSE 5173

# Development command
CMD ["npm", "run", "dev", "--", "--host"]
