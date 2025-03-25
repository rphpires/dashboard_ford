from utils.tracer import trace
from data.weekly_processor import process_weekly_data
import os
import sys
import time
import schedule
import logging
from datetime import datetime

# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Configurar logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "weekly_processor.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("weekly_processor")


def job():
    """Função a ser executada no agendamento."""
    logger.info("Iniciando processamento semanal de dados")
    try:
        success = process_weekly_data()
        if success:
            logger.info("Processamento semanal concluído com sucesso")
        else:
            logger.error("Falha no processamento semanal")
    except Exception as e:
        logger.exception(f"Erro durante o processamento semanal: {str(e)}")


def main():
    """Função principal para agendar o processamento semanal."""
    logger.info("Inicializando agendador de processamento semanal")

    # Agendar para todas as segundas-feiras às 00:15
    # Usamos 00:15 em vez de 00:00 para garantir que não haja conflito com outras tarefas de virada do dia
    schedule.every().monday.at("00:15").do(job)

    logger.info("Agendamento configurado: toda segunda-feira às 00:15")

    # Executar imediatamente na primeira vez se desejado (opcional)
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        logger.info("Executando processamento inicial imediato")
        job()

    # Loop principal para manter o agendador em execução
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Agendador interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Erro fatal no agendador: {str(e)}")
        sys.exit(1)
