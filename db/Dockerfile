FROM postgres:18-alpine

# Install build dependencies for pgvector
RUN apk add --no-cache \
    build-base \
    postgresql18-dev \
    git \
    clang19 \
    llvm19-dev

# Clone and install pgvector (latest master for PG18 compatibility)
RUN git clone https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && \
    make install && \
    rm -rf /tmp/pgvector
