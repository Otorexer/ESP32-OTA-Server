# Use smallest official Node.js image
FROM node:22-alpine

# Set working directory
WORKDIR /usr/src/app

# Only copy package files first, for efficient caching
COPY package.json ./

# Install only production dependencies
RUN npm install --production && npm cache clean --force

# Copy only server files (exclude frontend, public, .git, .repomix, etc.)
COPY index.js ./
COPY endpoints ./endpoints

# Remove any build-time only files if needed
# (But above pattern already excludes them)

# Expose port
EXPOSE 3000

# Start server
CMD ["npm", "start"]
