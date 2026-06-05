FROM node:20-bookworm-slim

# Chromium deps for Remotion headless render
RUN apt-get update && apt-get install -y \
    chromium \
    ca-certificates \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV CHROME_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /srv

# Renderer HTTP service
COPY package.json .
RUN npm install

COPY server.mjs .

# slides-cientificos mounted at /slides at runtime
EXPOSE 3000

CMD ["node", "server.mjs"]
