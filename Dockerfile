# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir dnslib

# Make port 53 available to the world outside this container
EXPOSE 53/udp


# Run python-dns.py when the container launches
CMD ["python", "merge-dns-server.py"]