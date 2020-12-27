FROM python:3.9

# Set working directory
WORKDIR /usr/src/app

# Copy all of the projects contents to containers /usr/src/app directory
COPY . .

# Install libraries from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run bot.py
CMD ["python", "bot.py"]
