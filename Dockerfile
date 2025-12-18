FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system deps including Chromium and Chromedriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates gnupg unzip curl xz-utils \
    chromium chromium-driver \
  && rm -rf /var/lib/apt/lists/*

# Set Chromium paths used by the app
ENV CHROME_BINARY=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

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
