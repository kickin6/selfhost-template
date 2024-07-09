# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /celery

# Copy the requirements file from the celery directory and install dependencies
COPY celery/requirements.txt /celery/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the celery directory contents into the container at /celery
COPY . /celery

# Also copy the app directory contents into the container at /app
COPY ../app /app

# Define environment variable to ensure app can be found
ENV PYTHONPATH="/celery:/app"

# Run the celery worker when the container launches
CMD ["celery", "-A", "celery", "worker", "--loglevel=info"]
