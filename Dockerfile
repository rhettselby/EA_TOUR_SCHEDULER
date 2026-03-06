FROM python:3.13-slim

# Install Chrome and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    nodejs \
    npm \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Build React and collect static files
RUN npm install --prefix frontend
RUN npm run build --prefix frontend
RUN python manage.py collectstatic --noinput