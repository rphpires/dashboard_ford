FROM python:3.10-slim

WORKDIR /app

# Instalar FreeTDS e suas dependências
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    tdsodbc \
    gcc \
    g++ \
    --reinstall build-essential \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Configurar o FreeTDS no odbcinst.ini
RUN echo "[FreeTDS]\n\
Description = FreeTDS unixODBC Driver\n\
Driver = /usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
Setup = /usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini

# Configurar a conexão com SQL Server no freetds.conf
RUN echo "[global]\n\
tds version = 8.0\n\
client charset = UTF-8\n\
text size = 20971520\n\
\n\
[MSSQL]\n\
host = host.docker.internal\n\
port = 1433\n\
tds version = 8.0" > /etc/freetds/freetds.conf

# Configurar DSN no odbc.ini
RUN echo "[MSSQL]\n\
Driver = FreeTDS\n\
Description = MS SQL Server\n\
Trace = No\n\
Server = host.docker.internal\n\
Port = 1433\n\
Database = W_Access\n\
TDS_Version = 8.0" > /etc/odbc.ini

# Copiar apenas os requisitos primeiro para aproveitar o cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código
COPY . .

# Criar script de inicialização
RUN echo '#!/bin/bash\n\
echo "Iniciando Dashboard Ford..."\n\
\n\
# Verificar configurações de conectividade\n\
echo "Testando conexão com SQL Server..."\n\
if [ -x "$(command -v tsql)" ]; then\n\
  echo "Testando via tsql:"\n\
  tsql -H ${DB_SERVER:-host.docker.internal} -p 1433 -U ${DB_USERNAME:-sa} -P "${DB_PASSWORD:-#w_access_Adm#}" -t "SELECT @@version"\n\
fi\n\
\n\
echo "Informações do driver ODBC:"\n\
odbcinst -j\n\
\n\
# Iniciar a aplicação\n\
exec python app.py' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Porta na qual o Dash irá rodar
EXPOSE 8050

# Usar o script de inicialização como ponto de entrada
ENTRYPOINT ["/app/entrypoint.sh"]