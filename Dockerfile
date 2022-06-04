FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Create directory and volume to persist the reader database
RUN mkdir -p /usr/src/app/reader
VOLUME /usr/src/app/reader

# Copy all of the projects contents to containers /usr/src/app directory
COPY . .

# Install libraries from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run bot.py
CMD ["python", "bot.py"]
