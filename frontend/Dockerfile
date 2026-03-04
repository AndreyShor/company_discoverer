FROM node:23.11.0-slim

# Set working directory inside container
WORKDIR /app

# Copy package.json and lock file separately for caching
COPY package*.json ./

# Install node dependencies (this installs react-scripts too)
RUN npm install

# Copy the rest of the frontend app
COPY . .

# Expose the port React runs on
EXPOSE 3000

# Run dev server
CMD ["npm", "start"]