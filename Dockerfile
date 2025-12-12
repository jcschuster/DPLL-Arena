FROM elixir:1.19.4-slim AS elixir_source

FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    time \
    libsctp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=elixir_source /usr/local /usr/local

RUN pip3 install --no-cache-dir cnfgen pandas matplotlib python-sat

WORKDIR /app

COPY runner.py /app/runner.py
RUN chmod +x /app/runner.py

RUN mkdir -p /app/solvers /app/results /app/problems

ENTRYPOINT ["python", "/app/runner.py"]