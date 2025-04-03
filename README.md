# Dashboard Ford

Dashboard interativo para visualização de utilização e disponibilidade de pistas de testes (tracks).

## Visão Geral

Este projeto implementa um dashboard web em Python usando Dash para visualizar:
- Utilização mensal e anual de pistas
- Disponibilidade de pistas
- Utilização por diferentes tipos de pistas
- Detalhamento por áreas de negócio, programas e equipes
- Análise de clientes internos e externos

## Estrutura do Projeto

```
dashboard/
├── app.py                  # Arquivo principal - inicializa e executa o app
├── config.py               # Configurações e cores do dashboard
├── data/
│   ├── __init__.py         # Torna o diretório um pacote Python
│   ├── mock_data.py        # Dados simulados para o dashboard
│   └── database.py         # Funções de conexão com banco de dados (futuro)
├── layouts/
│   ├── __init__.py         # Torna o diretório um pacote Python
│   ├── header.py           # Layout do cabeçalho
│   ├── left_column.py      # Layout da coluna esquerda
│   └── right_column.py     # Layout da coluna direita
├── components/
│   ├── __init__.py         # Torna o diretório um pacote Python
│   ├── graphs.py           # Funções para criar gráficos
│   └── sections.py         # Componentes de seções reutilizáveis
├── assets/
│   └── custom.css          # Estilos CSS personalizados
└── requirements.txt        # Dependências do projeto
```

## Pré-requisitos

- Python 3.8+
- pip (gerenciador de pacotes do Python)

## Instalação

1. Clone o repositório:
```
```

2. Crie e ative um ambiente virtual (recomendado):
```
# No Windows
python -m venv venv
venv\Scripts\activate

# No macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

## Execução

Execute o seguinte comando na raiz do projeto:
```
python app.py
```

O dashboard estará disponível em seu navegador no endereço `http://127.0.0.1:8050/`

## Estrutura do Código

- **app.py**: Arquivo principal que carrega os dados, monta o layout e executa o servidor
- **config.py**: Contém configurações globais como cores e valores estáticos
- **data/**: Módulos para carregar e processar dados
  - **mock_data.py**: Dados simulados para o desenvolvimento
  - **database.py**: Funções para conectar ao SQL Server no futuro
- **layouts/**: Componentes de layout de alto nível
  - **header.py**: Layout do cabeçalho
  - **left_column.py**: Layout da coluna esquerda do dashboard
  - **right_column.py**: Layout da coluna direita do dashboard
- **components/**: Componentes reutilizáveis
  - **graphs.py**: Funções para criar diferentes tipos de gráficos
  - **sections.py**: Funções para criar containers e seções do layout

## Conexão com SQL Server (Futuro)

Para conectar o dashboard ao SQL Server, você precisará:

1. Instalar os drivers ODBC para SQL Server
2. Configurar as variáveis de ambiente:
   - `DB_SERVER`: Nome/endereço do servidor
   - `DB_NAME`: Nome do banco de dados
   - `DB_USER`: Nome de usuário
   - `DB_PASSWORD`: Senha

Ou modifique diretamente o arquivo `data/database.py` com suas credenciais.

## Personalização

- Modifique o arquivo `assets/custom.css` para alterar o estilo visual
- Edite as cores e o layout no arquivo `config.py`
- Atualize os dados de exemplo no arquivo `data/mock_data.py`