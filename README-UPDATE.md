# Instruções para o novo Módulo de Gerenciamento de EJAs

Foi adicionado um novo módulo ao dashboard que permite gerenciar (adicionar, editar, excluir e importar) os dados de EJAs que anteriormente estavam apenas disponíveis através do arquivo CSV estático.

## Como acessar o gerenciador de EJAs

1. Execute o dashboard com `python app.py`
2. No navegador, você verá uma nova aba chamada "Gerenciar EJAs" no topo da página
3. Clique nessa aba para acessar o gerenciador

## Funcionalidades disponíveis

- **Buscar EJAs**: Utilize os campos de busca por título ou código EJA
- **Adicionar EJA**: Clique no botão "Adicionar EJA" para criar uma nova entrada
- **Editar EJA**: Clique no botão "Editar" na linha correspondente ao EJA que deseja modificar
- **Excluir EJA**: Clique no botão "Excluir" e confirme a exclusão
- **Importar CSV**: Faça upload de um arquivo CSV com dados de EJA
- **Exportar CSV**: Exporte os dados atuais para um arquivo CSV

## Importação de dados

Ao importar um arquivo CSV, você tem duas opções:
1. **Sobrescrever todos os dados existentes**: Substitui completamente os dados atuais
2. **Adicionar/atualizar apenas**: Mantém os dados existentes e apenas adiciona novos ou atualiza registros com mesmo EJA CODE

O arquivo CSV deve conter pelo menos as seguintes colunas:
- `EJA CODE`: Código numérico do EJA
- `TITLE`: Nome/título do EJA
- `NEW CLASSIFICATION`: Classificação do EJA

## Script de Backup

Um script utilitário foi adicionado para facilitar operações de backup e restauração pela linha de comando:

```bash
# Criar um backup
python scripts/eja_backup.py backup

# Listar backups disponíveis
python scripts/eja_backup.py list

# Restaurar a partir de um backup
python scripts/eja_backup.py restore

# Restaurar a partir de um arquivo específico sem sobrescrever dados
python scripts/eja_backup.py restore path/to/file.csv --keep-existing
```

## Solução de problemas

### Problema com versões de bibliotecas

Se você encontrar erros relacionados a argumentos inesperados nos componentes do dash-bootstrap-components, certifique-se de que a versão instalada corresponde à versão especificada no arquivo requirements.txt:

```bash
pip install -r requirements.txt
```

Se o problema persistir, você pode verificar a versão instalada:

```bash
pip show dash-bootstrap-components
```

E atualizar o arquivo requirements.txt para corresponder à sua versão atual.

### Dados não são salvos

Verifique se o diretório `aux_files` existe e tem permissões de escrita. O aplicativo tentará criar o diretório automaticamente, mas pode falhar dependendo das permissões do sistema.

### Erros na importação de CSV

Certifique-se de que o arquivo CSV:
- Está no formato correto (UTF-8)
- Contém todas as colunas obrigatórias: EJA CODE, TITLE e NEW CLASSIFICATION
- Os valores de EJA CODE são numéricos