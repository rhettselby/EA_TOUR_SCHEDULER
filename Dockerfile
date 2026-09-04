FROM python:3.13-slim

# Install Chrome and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    nodejs \
    npm \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install the chromedriver that matches the Chrome we just installed.
# Pinning at build time keeps browser and driver in lockstep. Downloading the
# driver at runtime lets them drift apart, and a driver newer than the browser
# passes launch switches Chrome rejects, so Chrome exits during startup and
# Selenium reports "session not created: Chrome instance exited".
RUN CHROME_VERSION="$(google-chrome --version | grep -oE '[0-9]+(\.[0-9]+){3}')" \
    && CHROME_MAJOR="${CHROME_VERSION%%.*}" \
    && echo "Chrome ${CHROME_VERSION} installed, resolving chromedriver..." \
    && DRIVER_VERSION="$CHROME_VERSION" \
    && if ! curl -fsSL -o /tmp/chromedriver.zip \
         "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip"; then \
         DRIVER_VERSION="$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR}")" \
         && curl -fsSL -o /tmp/chromedriver.zip \
              "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip"; \
       fi \
    && unzip -q /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 \
    && echo "Pinned $(chromedriver --version) to $(google-chrome --version)"

# Consumed by tours/tasks.py so the browser/driver paths are never guessed.
ENV CHROME_BIN=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Build React and collect static files
RUN npm install --prefix frontend
RUN npm run build --prefix frontend
RUN python manage.py collectstatic --noinput
