FROM node:20-alpine

RUN apk add --no-cache ffmpeg curl

WORKDIR /srv
COPY package.json .
RUN npm install

COPY server.mjs .

EXPOSE 3000
CMD ["node", "server.mjs"]
