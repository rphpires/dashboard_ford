# scripts/eja_backup.py
# Script para backup e restauração de dados EJA
from utils.tracer import trace, report_exception
from data.eja_manager import EJAManager
import os
import sys
import argparse
import datetime

# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_backup():
    """Cria um backup dos EJAs atuais"""
    try:
        eja_manager = EJAManager()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_file = os.path.join(backup_dir, f"eja_backup_{timestamp}.csv")
        file_path = eja_manager.export_csv(backup_file)

        print(f"Backup criado com sucesso: {file_path}")
        return file_path
    except Exception as e:
        report_exception(e)
        print(f"Erro ao criar backup: {str(e)}")
        return None


def restore_from_backup(backup_file, overwrite=True):
    """Restaura os EJAs a partir de um arquivo de backup"""
    try:
        if not os.path.exists(backup_file):
            print(f"Arquivo de backup não encontrado: {backup_file}")
            return False

        eja_manager = EJAManager()
        result = eja_manager.import_csv(backup_file, overwrite=overwrite)

        if 'error' in result:
            print(f"Erro ao restaurar backup: {result['error']}")
            return False

        print(f"Backup restaurado com sucesso!")
        if overwrite:
            print(f"- {result.get('imported', 0)} registros importados.")
        else:
            print(f"- {result.get('imported', 0)} adicionados.")
            print(f"- {result.get('updated', 0)} atualizados.")
            print(f"- {result.get('skipped', 0)} ignorados.")

        return True
    except Exception as e:
        report_exception(e)
        print(f"Erro ao restaurar backup: {str(e)}")
        return False


def list_backups():
    """Lista todos os backups disponíveis"""
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        if not os.path.exists(backup_dir):
            print("Nenhum backup encontrado.")
            return []

        backups = [f for f in os.listdir(backup_dir) if f.startswith("eja_backup_") and f.endswith(".csv")]

        if not backups:
            print("Nenhum backup encontrado.")
            return []

        print("\nBackups disponíveis:")
        for i, backup in enumerate(backups, 1):
            # Extrair timestamp do nome do arquivo
            timestamp = backup.replace("eja_backup_", "").replace(".csv", "")
            try:
                date_time = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                formatted_date = date_time.strftime("%d/%m/%Y %H:%M:%S")
            except:
                formatted_date = timestamp

            print(f"{i}. {backup} ({formatted_date})")

        print()  # Linha em branco
        return [os.path.join(backup_dir, b) for b in backups]
    except Exception as e:
        report_exception(e)
        print(f"Erro ao listar backups: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Gerenciador de backups de EJAs')
    subparsers = parser.add_subparsers(dest='command', help='Comando')

    # Comando para backup
    backup_parser = subparsers.add_parser('backup', help='Criar um backup dos EJAs atuais')

    # Comando para restauração
    restore_parser = subparsers.add_parser('restore', help='Restaurar EJAs a partir de um backup')
    restore_parser.add_argument('file', nargs='?', help='Arquivo de backup para restaurar')
    restore_parser.add_argument('--keep-existing', action='store_true',
                                help='Manter dados existentes e apenas adicionar novos/atualizar')

    # Comando para listar backups
    list_parser = subparsers.add_parser('list', help='Listar todos os backups disponíveis')

    args = parser.parse_args()

    if args.command == 'backup':
        create_backup()

    elif args.command == 'restore':
        if not args.file:
            # Se não foi especificado um arquivo, listar os disponíveis e perguntar
            backups = list_backups()
            if not backups:
                return

            while True:
                try:
                    choice = input("Digite o número do backup a ser restaurado (ou 'q' para sair): ")
                    if choice.lower() == 'q':
                        return

                    choice = int(choice)
                    if 1 <= choice <= len(backups):
                        selected_backup = backups[choice - 1]
                        break
                    else:
                        print("Número inválido. Tente novamente.")
                except ValueError:
                    print("Entrada inválida. Digite um número ou 'q'.")
        else:
            selected_backup = args.file

        # Confirmar sobrescrita
        if not args.keep_existing:
            confirm = input("ATENÇÃO: Esta ação irá sobrescrever todos os dados existentes. Continuar? (s/n): ")
            if confirm.lower() != 's':
                print("Operação cancelada.")
                return

        # Restaurar o backup
        restore_from_backup(selected_backup, overwrite=not args.keep_existing)

    elif args.command == 'list':
        list_backups()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
