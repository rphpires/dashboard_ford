from utils.db_connection import *
from utils.tracer import *
import pandas as pd
import json


class EJAReportGenerator:
    """
    Classe para gerar relatórios de horas trabalhadas por classificação EJA.
    """

    def __init__(self, dashboard_df=None, eja_df=None, dashboard_file=None, eja_file=None):
        """
        Inicializa o gerador de relatórios.

        Args:
            dashboard_df (DataFrame, opcional): DataFrame com os dados do dashboard
            eja_df (DataFrame, opcional): DataFrame com os dados de EJA
            dashboard_file (str, opcional): Caminho para o arquivo dashboard_ford.csv
            eja_file (str, opcional): Caminho para o arquivo eja_simplificado.csv
        """
        # Se fornecidos DataFrames, usar diretamente
        self.dashboard_df = dashboard_df
        self.eja_df = eja_df

        # Se fornecidos caminhos de arquivo, carregar os DataFrames
        if dashboard_file and not dashboard_df:
            self.dashboard_df = pd.read_csv(dashboard_file, encoding='utf-8')

        if eja_file and not eja_df:
            self.eja_df = pd.read_csv(eja_file, encoding='utf-8')

        # Preparar os DataFrames
        if self.dashboard_df is not None and self.eja_df is not None:
            self._preparar_dataframes()

    def _preparar_dataframes(self):
        """Prepara os DataFrames para processamento, convertendo tipos de dados."""
        # Garantir tipos numéricos para as colunas de códigos
        self.eja_df['EJA CODE'] = pd.to_numeric(self.eja_df['EJA CODE'], errors='coerce')
        self.dashboard_df['EJA'] = pd.to_numeric(self.dashboard_df['EJA'], errors='coerce')

    @staticmethod
    def converter_tempo_para_horas(tempo_str):
        """Converte uma string de tempo no formato HH:MM para horas decimais."""
        try:
            if pd.isna(tempo_str) or tempo_str == "":
                return 0.0

            horas, minutos = map(int, tempo_str.split(':'))
            return horas + (minutos / 60.0)
        except Exception as ex:
            report_exception(ex)
            return 0.0

    def format_datetime(self, total_horas):
        # Converter para o formato HH:MM
        horas_inteiras = int(total_horas)  # Parte inteira das horas
        minutos = int((total_horas - horas_inteiras) * 60)  # Parte decimal convertida para minutos

        # Formatar como HH:MM
        return f"{horas_inteiras:02d}:{minutos:02d}"

    def gerar_relatorio(self, classificacao, top_n=7):
        """
        Gera um relatório com as horas por classificação.

        Args:
            classificacao (str): Valor de NEW CLASSIFICATION para filtrar
            top_n (int): Número de itens principais a retornar

        Returns:
            dict: Resultado do processamento
        """
        if self.dashboard_df is None or self.eja_df is None:
            return {"error": "DataFrames não inicializados"}

        dashboard_copy = self.dashboard_df.copy()
        dashboard_copy['HorasDecimais'] = dashboard_copy['StayTime'].apply(self.converter_tempo_para_horas)

        # Converter para float para garantir a compatibilidade de tipos
        total_horas_geral = float(dashboard_copy['HorasDecimais'].sum())

        # Filtrar EJA por classificação
        eja_filtrado = self.eja_df[self.eja_df['NEW CLASSIFICATION'] == classificacao]

        if len(eja_filtrado) == 0:
            return {"error": f"Nenhum registro encontrado com a classificação '{classificacao}'"}

        # Lista de EJA CODEs que pertencem à classificação desejada
        eja_codes_da_classificacao = set(eja_filtrado['EJA CODE'].tolist())

        # Filtrar registros do dashboard que têm EJA correspondente na classificação
        dashboard_filtrado = self.dashboard_df[self.dashboard_df['EJA'].isin(eja_codes_da_classificacao)]

        if len(dashboard_filtrado) == 0:
            return {"error": f"Nenhum registro no dashboard corresponde à classificação '{classificacao}'"}

        # Converter a coluna StayTime para horas decimais
        dashboard_filtrado['HorasDecimais'] = dashboard_filtrado['StayTime'].apply(self.converter_tempo_para_horas)

        # Agrupar por EJA e somar as horas
        horas_por_eja = dashboard_filtrado.groupby('EJA')['HorasDecimais'].sum().reset_index()

        # Ordenar por horas (decrescente)
        horas_por_eja = horas_por_eja.sort_values('HorasDecimais', ascending=False)

        # Calcular o total de horas
        total_horas = self.format_datetime(horas_por_eja['HorasDecimais'].sum())
        _total_horas = float(horas_por_eja['HorasDecimais'].sum())

        # Pegar os top_n itens com mais horas
        top_itens = horas_por_eja.head(top_n)

        # Calcular a porcentagem em relação ao total
        porcentagem = (_total_horas / total_horas_geral) * 100 if total_horas_geral > 0 else 0

        # Criar lista de resultados com título do EJA
        resultado_top = []
        for _, row in top_itens.iterrows():
            eja_code = row['EJA']
            # Buscar o título correspondente ao EJA CODE
            titulo_encontrado = self.eja_df[self.eja_df['EJA CODE'] == eja_code]['TITLE']
            titulo = titulo_encontrado.iloc[0] if not titulo_encontrado.empty else "Título não encontrado"

            resultado_top.append({
                "EJA_CODE": int(eja_code) if pd.notna(eja_code) else None,
                "TITLE": titulo,
                "HORAS": self.format_datetime(row['HorasDecimais'])
            })

        # Montar o resultado final
        resultado = {
            "classificacao": classificacao,
            "total_horas": total_horas,
            "porcentagem": f"{porcentagem:.1f}%",
            "top_7_itens": resultado_top
        }

        return resultado


# Script principal
def main():
    # Conectar ao banco e obter os dados
    sql = DatabaseReader()

    start_date = '2024-01-01 00:00:33.220'
    end_date = '2024-01-31 23:59:59.220'

    # Obter dados da SP
    results_df = sql.execute_stored_procedure_df("sp_VehicleAccessReport", [start_date, end_date])
    print(f"Total={len(results_df)}")

    # # Salvar os resultados em CSV para referência
    # results_df.to_csv('dashboard_ford.csv', index=False, encoding='utf-8-sig')
    # print("Dashboard data saved to dashboard_ford.csv")

    # Ler o arquivo de EJA auxiliar
    eja_path = os.path.join(os.path.dirname(__file__), "aux_files", "eja_simplificado.csv")
    eja_df = pd.read_csv(eja_path, encoding='utf-8')

    # Criar o gerador de relatórios
    report_gen = EJAReportGenerator(dashboard_df=results_df, eja_df=eja_df)

    # Gerar relatório para a classificação "PROGRAMS"
    classificacao = "INTERNAL USERS"
    resultado = report_gen.gerar_relatorio(classificacao)

    # Exibir o resultado
    print(json.dumps(resultado, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
