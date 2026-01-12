# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install uv (our package manager)
RUN pip install uv

# Copy the uv.lock file and pyproject.toml (if using poetry/uv)
COPY uv.lock pyproject.toml ./

# Install project dependencies
RUN uv pip install --system --no-deps

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=development

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]