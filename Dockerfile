FROM python:3.11.4-slim
WORKDIR /app

# Switch off interaction with UI when libs are updated (modal windows)
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get clean && apt-get update \
    && apt-get -y install --no-install-recommends \
        build-essential \
    && apt-get clean \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/cache/apt/*

# Install libs    
COPY requirements.txt requirements.txt

RUN python3 -m pip --no-cache-dir install --upgrade pip==22.3.1 && \
    python3 -m pip --no-cache-dir install -r requirements.txt

# Create non-route user for more security 
# Create `app` folder with owner `app`
RUN groupadd -g 1001 -r app && \
    useradd -u 1001 -r -d /app -g app app && \
    mkdir -p /app && \
    chown -R app:app /app

# Copy local app folder to docker folder app
COPY --chown=app . .

# Define env var and swithch to the 'app' user
ENV PYTHONPATH=":/app"
USER app

# Expose app at defined port, and define commands
EXPOSE 5000