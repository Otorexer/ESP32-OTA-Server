# Use an official Node.js runtime as a parent image
FROM node:22

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if exists)
COPY package.json ./

# Install dependencies
RUN npm install --production

# Copy the rest of the application code (but NOT frontend or public)
COPY . .

# Remove frontend and public from the image (we will mount as volumes)
RUN rm -rf frontend public

# Expose the server port
EXPOSE 3000

# Run the server
CMD [ "npm", "start" ]
