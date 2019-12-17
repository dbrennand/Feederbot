FROM python:3.7

WORKDIR /usr/src/app

# Copy all of projects contents to containers /usr/src/app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Run bot.py
CMD ["python", "bot.py"]