# Use smallest official Node.js image
FROM node:22-alpine
RUN apk add --no-cache wget

# Set working directory
WORKDIR /usr/src/app

# Only copy package files first, for efficient caching
COPY package.json ./

# Set environment for production
ENV NODE_ENV=production

# Install only production dependencies
RUN npm install --production && npm cache clean --force

# Copy only server files (exclude frontend, public, .git, .repomix, etc.)
COPY index.js ./
COPY endpoints ./endpoints

# Remove any build-time only files if needed
# (But above pattern already excludes them)

# Expose port
EXPOSE 3000

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ping || exit 1

# Start server
CMD ["npm", "start"]
