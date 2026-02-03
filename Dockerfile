# Use your existing setup...
FROM elixir:1.19.4-slim AS elixir_source
FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    time \
    libsctp1 \
    libncurses6 \
    libstdc++6\
    locales \
    && rm -rf /var/lib/apt/lists/*

# Locale setup
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# Copy Elixir
COPY --from=elixir_source /usr/local /usr/local

# Python Deps
RUN pip3 install --no-cache-dir cnfgen pandas matplotlib python-sat streamlit plotly

WORKDIR /app
ENV HOME=/root

# Create Directories
RUN mkdir -p /app/solvers /app/results /app/problems

# Copy Files
COPY engine.py /app/engine.py
COPY app.py /app/app.py
# (Optional: Copy a folder of default problems/solvers if you want them pre-loaded)

# Expose Streamlit Port
EXPOSE 8501

# ENTRYPOINT: Run Streamlit directly
ENTRYPOINT ["streamlit", "run", "/app/app.py", "--server.address=0.0.0.0"]