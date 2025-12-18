FROM elixir:1.19.4-slim AS elixir_source

FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    time \
    libsctp1 \
    libncurses6 \
    libstdc++6\
    locales \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY --from=elixir_source /usr/local /usr/local

RUN pip3 install --no-cache-dir cnfgen pandas matplotlib python-sat streamlit plotly

WORKDIR /app

ENV HOME=/root

COPY runner.py /app/runner.py
RUN chmod +x /app/runner.py

COPY dashboard.py /app/dashboard.py
RUN chmod +x /app/dashboard.py

RUN mkdir -p /app/solvers /app/results /app/problems

ENTRYPOINT ["python", "/app/runner.py"]