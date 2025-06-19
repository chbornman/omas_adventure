FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Clean any existing build and build fresh
RUN rm -rf build/ && \
    pygbag --build --app_name "Oma's Adventure" --ume_block 0 --can_close 1 . && \
    ls -la build/web/ && \
    echo "Build completed successfully"

# Download pygame-web CDN files to exactly where the JS expects them
RUN mkdir -p build/web/archives/0.9/vt && \
    curl -L -o build/web/archives/0.9/pythons.js https://pygame-web.github.io/archives/0.9/pythons.js || true && \
    curl -L -o build/web/archives/0.9/browserfs.min.js https://pygame-web.github.io/archives/0.9/browserfs.min.js || true && \
    curl -L -o build/web/archives/0.9/pythonrc.py https://pygame-web.github.io/archives/0.9/pythonrc.py || true && \
    curl -L -o build/web/archives/0.9/vt/xterm.js https://pygame-web.github.io/archives/0.9/vt/xterm.js || true && \
    curl -L -o build/web/archives/0.9/vt/xterm-addon-image.js https://pygame-web.github.io/archives/0.9/vt/xterm-addon-image.js || true

# Expose web port
EXPOSE 8080

# Serve with Python's built-in server
CMD ["python", "-m", "http.server", "8080", "-d", "build/web", "-b", "0.0.0.0"]