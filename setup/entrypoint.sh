#!/bin/bash
# Script de inicialização para o container

# Verificar se existem variáveis de ambiente para configuração do banco
if [ ! -z "$DB_SERVER" ] && [ ! -z "$DB_DATABASE" ]; then
  echo "Aplicando configurações de banco de dados a partir de variáveis de ambiente..."
  
  # Criar/atualizar o arquivo de configuração
  mkdir -p /app/config
  cat > /app/config/db_connection.cfg << EOF
[config]
WAccessBDServer = $DB_SERVER
WAccessDB = $DB_DATABASE
EOF

  echo "Configuração do banco de dados atualizada."
fi

# Configurar o driver ODBC para FreeTDS
echo "Configurando driver ODBC..."
cat > /etc/odbc.ini << EOF
[ODBC Data Sources]
SQLServerDB = FreeTDS

[SQLServerDB]
Driver = FreeTDS
Description = SQL Server via FreeTDS
Server = $DB_SERVER
Database = $DB_DATABASE
TDS_Version = 8.0
EOF

# Iniciar a aplicação
echo "Iniciando Dashboard Ford..."
exec python app.py