# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Create a simple Python script
RUN echo 'print("Hello from inside the Docker container!")' > app.py

# Set the default command to run the script
CMD ["python", "app.py"]
