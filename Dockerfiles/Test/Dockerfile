# syntax=docker/dockerfile:1

FROM alpine:3.19

# Set up a simple script as the entrypoint
RUN echo -e '#!/bin/sh\necho "hello world"' > /hello.sh && \
    chmod +x /hello.sh

ENTRYPOINT ["/hello.sh"]
