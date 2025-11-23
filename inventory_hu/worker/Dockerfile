FROM node:18-alpine

WORKDIR /usr/src/app

COPY package.json tsconfig.json ./
RUN npm install --production

COPY src ./src

CMD ["npm", "run", "start"]
