# Build Application Container
FROM alpine:3

# Setup Python
# hadolint ignore=DL3018
RUN apk add -U --no-cache python3 && \
    addgroup -g 1000 app && \
    adduser -D -u 1000 -G app app && \
    mkdir /app

# Install Application
COPY app/* /app/
WORKDIR /app

# hadolint ignore=DL3018
RUN chown -R app:app /app && \
    apk --no-cache add --virtual build-deps gcc musl-dev && \
    pip3 install -r requirements.txt --upgrade pip && \
    apk del build-deps

# Image Settings
USER app
ENTRYPOINT ["python3"]
CMD ["vault-sidecar.py"]
