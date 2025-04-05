# Guia de Instalação e Configuração do Dashboard Ford

Este guia orienta você na instalação e configuração do Dashboard Ford usando Docker.

## Pré-requisitos

- **Docker Desktop**: Necessário para executar o dashboard.
  - [Download do Docker Desktop para Windows](https://www.docker.com/products/docker-desktop)
  - Após instalar, reinicie o computador

## Instalação

1. **Extraia todos os arquivos** do pacote de instalação em uma pasta de sua escolha.

2. **Execute o gerenciador do dashboard**: 
   - Dê um duplo clique no arquivo `manage_dashboard.bat`
   - Este utilitário permite iniciar, parar e configurar o dashboard

## Configuração do Banco de Dados

### Opção 1: Usando o gerenciador (Recomendado)

1. No menu do gerenciador, selecione a opção **3. Configurar Conexão com Banco de Dados**
2. Informe os dados solicitados:
   - **Servidor**: Endereço do servidor SQL Server (ex: `localhost,1433` ou `192.168.1.10`)
   - **Nome do Banco de Dados**: Nome do banco de dados
   - **Usuário**: Nome de usuário para acessar o banco
   - **Senha**: Senha para acessar o banco
3. Confirme as informações quando solicitado
4. O dashboard será reiniciado automaticamente com as novas configurações

### Opção 2: Configuração manual

1. Acesse a pasta `config` e abra o arquivo `db_connection.cfg` em um editor de texto
2. Modifique as configurações conforme necessário:
   ```
   [DATABASE]
   SERVER = seu_servidor,1433
   DATABASE = seu_banco
   DRIVER = ODBC Driver 17 for SQL Server
   TRUSTED_CONNECTION = no
   UID = seu_usuario
   PWD = sua_senha
   ```
3. Salve o arquivo e reinicie o dashboard pelo gerenciador (opção 5)

## Uso

1. **Iniciar o Dashboard**:
   - No gerenciador, selecione a opção **1. Iniciar Dashboard**
   - Aguarde alguns segundos para que o sistema inicie completamente

2. **Acessar o Dashboard**:
   - Abra um navegador web (Chrome, Firefox, Edge, etc.)
   - Digite o endereço: `http://localhost:8050`

3. **Parar o Dashboard**:
   - No gerenciador, selecione a opção **2. Parar Dashboard**

## Solução de Problemas

Se o dashboard não iniciar ou apresentar problemas:

1. **Verifique os logs**:
   - No gerenciador, selecione a opção **4. Ver Logs**
   - Examine as mensagens de erro para identificar o problema

2. **Problemas de conexão com o banco de dados**:
   - Verifique se o servidor de banco de dados está acessível
   - Confirme se as credenciais estão corretas
   - Certifique-se de que o firewall não está bloqueando a conexão

3. **Suporte**:
   - Para suporte adicional, envie os logs para nossa equipe de suporte:
   - Email: suporte@empresa.com
   - Telefone: (XX) XXXX-XXXX

## Atualizações

Para atualizar o dashboard para uma nova versão:

1. Faça backup das suas configurações:
   - Copie o conteúdo da pasta `config`
   - Salve o arquivo `.env` se existir
2. Instale a nova versão
3. Restaure suas configurações

## Limitações

- O dashboard requer conectividade com o banco de dados SQL Server
- Conexões ao banco de dados local podem exigir a configuração do SQL Server para permitir conexões remotas