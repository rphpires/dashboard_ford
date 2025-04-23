FROM python:3.10-slim

WORKDIR /app

# Preparar ambiente para drivers ODBC
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    tdsodbc \
    freetds-bin \
    freetds-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar FreeTDS - configuração básica necessária
RUN echo "[FreeTDS]\nDescription = FreeTDS Driver\nDriver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\nSetup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so\nUsageCount = 1" > /etc/odbcinst.ini

# Configurar freetds.conf para melhorar a compatibilidade com SQL Server
RUN echo "[global]\ntds version = 8.0\nclient charset = UTF-8\ntext size = 20971520" > /etc/freetds/freetds.conf

# Copiar apenas os requisitos primeiro para aproveitar o cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Porta na qual o Dash irá rodar
EXPOSE 8050

ENV DB_SERVER=localhost \
    DB_PORT=1433 \
    DB_DATABASE=W_Access \
    DB_USERNAME=sa \
    DB_PASSWORD=#w_access_Adm# \
    DASH_DEBUG=false \
    DASH_HOST=0.0.0.0

# Comando para iniciar a aplicação
CMD ["python", "app.py"]