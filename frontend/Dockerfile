# 构建阶段
FROM node:20-bookworm-slim AS build
WORKDIR /src

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# 生产构建：空表示走相对路径 /api，由前置 Nginx 反代到后端
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# 运行阶段
FROM nginx:1.26-alpine
COPY --from=build /src/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
