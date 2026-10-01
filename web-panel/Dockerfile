# Staff web panel: built with Node, served by nginx, which also forwards /api and /p/ to the backend.
#   docker build -t madare-emrooz-web .
#   docker run -p 8080:80 -e BACKEND_URL=http://backend:5000 madare-emrooz-web

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
# Where nginx forwards API calls; replaced in the config template when the container starts.
ENV BACKEND_URL=http://backend:5000
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
