# CARA frontend — production image (self-hosted option)
# Builds the static Vite bundle, then serves it with nginx.
#
# IMPORTANT: VITE_API_URL is baked in at BUILD time, not runtime, because
# Vite inlines import.meta.env.* into the compiled JS. Pass it as a build
# arg pointing at your deployed backend's public URL before building this
# image. If you deploy the frontend on Vercel/Netlify instead (recommended
# for most cases — see DEPLOYMENT.md), you don't need this file at all.

FROM node:20-slim AS build
WORKDIR /app

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# TanStack Router is a client-side SPA — any unknown path must fall back to
# index.html so client-side routing (e.g. a direct link to /voice) works.
RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
