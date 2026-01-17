# Use official Python image (slim version is smaller)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed, e.g. for git or gcc)
# RUN apt-get update && apt-get install -y gcc

# Copy requirements first (better cache usage)
COPY bot/requirements.txt requirements.txt

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variable for unbuffered output
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "-m", "bot.main"]
