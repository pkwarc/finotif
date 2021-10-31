FROM nginx:1.20-alpine

COPY nginx.default.conf /etc/nginx/conf.d/
COPY nginx-entrypoint.sh /

RUN chmod +x /nginx-entrypoint.sh

ENTRYPOINT ["/nginx-entrypoint.sh"]

CMD ["nginx", "-g", "daemon off;"]