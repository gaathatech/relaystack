FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system deps including Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates gnupg unzip curl xz-utils \
  && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update && apt-get install -y google-chrome-stable \
  && rm -rf /var/lib/apt/lists/*

# Set Chrome paths used by the app
ENV CHROME_BINARY=/usr/bin/google-chrome

# Install python deps
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

# Copy app
COPY . /app

# Ensure sessions and logs directories exist
RUN mkdir -p /app/static/logs /app/user_data /app/sessions

# Expose port (Render will provide via $PORT env)
EXPOSE 5000

# Start command uses $PORT if provided by environment
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
CMD ["/app/run.sh"]
