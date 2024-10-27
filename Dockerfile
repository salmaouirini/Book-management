# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code including .env
COPY . .

# Expose the port your app runs on
EXPOSE 5001

# Command to run the app
CMD ["gunicorn", "-b", "0.0.0.0:5001", "app:app"]
