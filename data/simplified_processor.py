# data/simplified_processor.py
# Processador simplificado para dados da SP - substitui o ReportGenerator complexo

import pandas as pd
from datetime import datetime
from utils.tracer import trace, report_exception
from data.local_db_handler import get_db_handler
from data.eja_manager import get_eja_manager


class SimplifiedDataProcessor:
    """
    Processador simplificado que trabalha diretamente com dados da SP,
    eliminando camadas desnecessárias de complexidade.
    """

    def __init__(self, dashboard_df):
        self.raw_df = dashboard_df.copy() if dashboard_df is not None else pd.DataFrame()
        self.eja_manager = get_eja_manager()

        # Cache de EJAs para lookup rápido
        self._eja_cache = {}
        self._load_eja_cache()

    def _load_eja_cache(self):
        """Carrega EJAs em cache para lookup rápido - CORRIGIDO"""
        try:
            all_ejas = self.eja_manager.get_all_ejas()

            # CORREÇÃO: Garantir que as chaves sejam strings consistentes
            self._eja_cache = {}
            for eja in all_ejas:
                eja_code = str(eja['eja_code']).strip()  # Sempre string, sem espaços
                self._eja_cache[eja_code] = eja

            trace(f"Cache de EJAs carregado: {len(self._eja_cache)} registros")

            # DEBUG: Verificar se os EJAs problemáticos estão no cache
            expected_ejas = ['832', '35', '36', '23', '6', '8', '12', '1']
            print(f"Verificando EJAs críticos no cache:")
            for eja in expected_ejas:
                if eja in self._eja_cache:
                    print(f"  ✅ EJA {eja}: {self._eja_cache[eja]['title']}")
                else:
                    print(f"  ❌ EJA {eja}: NÃO ENCONTRADO no cache")

        except Exception as e:
            trace(f"Erro ao carregar cache de EJAs: {e}", color="red")
            self._eja_cache = {}

    def _safe_time_to_hours(self, time_str):
        """
        Conversão segura e consistente de HH:MM para horas decimais
        Mantém logs para diagnóstico quando necessário
        """
        if pd.isna(time_str) or not time_str or ':' not in str(time_str):
            return 0.0

        try:
            parts = str(time_str).split(':')
            if len(parts) != 2:
                return 0.0

            hours = int(parts[0])
            minutes = int(parts[1])
            return hours + (minutes / 60.0)
        except (ValueError, TypeError):
            return 0.0

    def _filter_valid_data(self):
        """
        Aplica filtros básicos para dados válidos
        Equivale aos filtros da sua consulta SQL
        """
        if self.raw_df.empty:
            return pd.DataFrame()

        # Filtros equivalentes à sua consulta SQL
        filtered_df = self.raw_df[
            self.raw_df['StayTime'].notna()
            & (self.raw_df['StayTime'] != '')
            & self.raw_df['StayTime'].str.contains(':', na=False)
            & self.raw_df['VehicleExitTime'].notna()  # Equivale ao WHERE e.VehicleExitTime is not null
        ].copy()

        # Adicionar coluna de horas decimais
        filtered_df['HorasDecimais'] = filtered_df['StayTime'].apply(self._safe_time_to_hours)

        # Remover registros com 0 horas (dados inválidos)
        filtered_df = filtered_df[filtered_df['HorasDecimais'] > 0]

        trace(f"Dados filtrados: {len(filtered_df)} de {len(self.raw_df)} registros originais")
        return filtered_df

    def get_programs_data(self, top_n=7):
        """Dados para gráfico de Programs"""
        return self._get_classification_data("PROGRAMS", top_n)

    def get_other_skills_data(self, top_n=7):
        """Dados para gráfico de Other Skill Teams"""
        return self._get_classification_data("OTHER SKILL TEAMS", top_n)

    def get_internal_users_data(self, top_n=7):
        """Dados para gráfico de Internal Users"""
        return self._get_classification_data("INTERNAL USERS", top_n)

    def get_external_sales_data(self, top_n=7):
        """Dados para gráfico de External Sales"""
        return self._get_classification_data("EXTERNAL SALES", top_n)

    def _get_classification_data(self, classification, top_n=7):
        """
        Versão corrigida que garante consistência de tipos entre EJA e cache
        """
        filtered_df = self._filter_valid_data()

        if filtered_df.empty:
            return pd.DataFrame(columns=['title', 'hours'])

        # Obter EJAs desta classificação do cache
        eja_codes = [
            code for code, eja in self._eja_cache.items()
            if eja.get('new_classification') == classification
        ]

        if not eja_codes:
            trace(f"Nenhum EJA encontrado para classificação: {classification}")
            return pd.DataFrame(columns=['title', 'hours'])

        # CORREÇÃO: Garantir que ambos estejam no mesmo tipo
        # Converter tanto os dados quanto o cache para string para comparação
        filtered_df['EJA_str'] = filtered_df['EJA'].astype(str).str.strip()
        eja_codes_str = [str(code).strip() for code in eja_codes]

        # DEBUG para PROGRAMS
        if classification == "PROGRAMS":
            print(f"\n=== DEBUG CORREÇÃO DE TIPOS ===")
            print(f"EJAs no cache (originais): {eja_codes[:5]}...")
            print(f"EJAs no cache (como string): {eja_codes_str[:5]}...")
            print(f"EJAs nos dados (únicos): {sorted(filtered_df['EJA_str'].unique())[:10]}...")
            print(f"Intersecção encontrada: {set(eja_codes_str) & set(filtered_df['EJA_str'].unique())}")

        # Filtrar dados por EJAs desta classificação
        classification_df = filtered_df[filtered_df['EJA_str'].isin(eja_codes_str)]

        if classification == "PROGRAMS":
            print(f"Registros encontrados após correção: {len(classification_df)}")
            if not classification_df.empty:
                total_hours = classification_df['HorasDecimais'].sum()
                print(f"Total de horas: {total_hours}")
            print("=== FIM DEBUG CORREÇÃO ===\n")

        if classification_df.empty:
            return pd.DataFrame(columns=['title', 'hours'])

        # Resto do código permanece igual...
        grouped = classification_df.groupby('EJA_str')['HorasDecimais'].sum().reset_index()
        grouped = grouped.sort_values('HorasDecimais', ascending=False).head(top_n)

        # Adicionar títulos dos EJAs
        result_data = []
        for _, row in grouped.iterrows():
            eja_code = row['EJA_str']
            eja_info = self._eja_cache.get(eja_code, {})

            # Nome da coluna depende do tipo de gráfico
            if classification == "PROGRAMS":
                key_name = 'program'
            elif classification == "OTHER SKILL TEAMS":
                key_name = 'team'
            elif classification == "INTERNAL USERS":
                key_name = 'department'
            else:  # EXTERNAL SALES
                key_name = 'company'

            result_data.append({
                key_name: eja_info.get('title', f'EJA {eja_code}'),
                'hours': int(row['HorasDecimais'])
            })

        return pd.DataFrame(result_data)

    def get_tracks_data(self):
        """
        Dados para gráfico de Tracks (LocalityName)
        Retorna dicionário no formato esperado pelos gráficos
        """
        filtered_df = self._filter_valid_data()

        if filtered_df.empty:
            return {}

        # Agrupar por LocalityName
        tracks_grouped = filtered_df.groupby('LocalityName')['HorasDecimais'].sum()

        # Converter para o formato esperado
        tracks_dict = {}
        for locality, hours in tracks_grouped.items():
            # Converter horas decimais de volta para HH:MM
            total_minutes = int(hours * 60)
            hours_part = total_minutes // 60
            minutes_part = total_minutes % 60
            time_formatted = f"{hours_part:02d}:{minutes_part:02d}"

            tracks_dict[str(locality)] = {
                'track_name': str(locality),
                'track_time': time_formatted
            }

        return tracks_dict

    def get_areas_data(self):
        """
        Dados para gráfico de Areas (VehicleDepartment)
        """
        filtered_df = self._filter_valid_data()

        if filtered_df.empty:
            return pd.DataFrame(columns=['area', 'hours'])

        # Agrupar por VehicleDepartment
        areas_grouped = filtered_df.groupby('VehicleDepartment')['HorasDecimais'].sum().reset_index()
        areas_grouped = areas_grouped.sort_values('HorasDecimais', ascending=False)

        # Renomear colunas e converter para inteiro
        areas_grouped = areas_grouped.rename(columns={
            'VehicleDepartment': 'area',
            'HorasDecimais': 'hours'
        })
        areas_grouped['hours'] = areas_grouped['hours'].astype(int)

        return areas_grouped

    def get_total_hours_formatted(self):
        """
        Retorna o total de horas no formato HH:MM
        """
        filtered_df = self._filter_valid_data()

        if filtered_df.empty:
            return "00:00"

        total_hours = filtered_df['HorasDecimais'].sum()
        total_minutes = int(total_hours * 60)
        hours_part = total_minutes // 60
        minutes_part = total_minutes % 60

        return f"{hours_part:02d}:{minutes_part:02d}"

    def get_all_dashboard_data(self):
        """
        Método principal que retorna todos os dados necessários para o dashboard
        no formato esperado pelos layouts existentes
        """
        try:
            # Processar todos os dados de uma vez
            programs_df = self.get_programs_data()
            other_skills_df = self.get_other_skills_data()
            internal_users_df = self.get_internal_users_data()
            external_sales_df = self.get_external_sales_data()

            tracks_data = self.get_tracks_data()
            areas_data = self.get_areas_data()
            total_hours = self.get_total_hours_formatted()

            # Montar no formato esperado pelo dashboard
            dfs = {
                'programs': programs_df,
                'other_skills': other_skills_df,
                'internal_users': internal_users_df,
                'external_sales': external_sales_df,
                'tracks_data': tracks_data,
                'areas_data_df': areas_data,
                'total_hours': total_hours
            }

            # Para compatibilidade, adicionar DataFrames vazios para utilização/disponibilidade
            # (estes continuarão vindo do SQLite como você mencionou)
            dfs['utilization'] = pd.DataFrame(columns=['month', 'utilization'])
            dfs['availability'] = pd.DataFrame(columns=['month', 'availability'])

            return dfs, tracks_data, areas_data, {
                'total_hours': total_hours,
                'total_hours_ytd': total_hours,
                'ytd_utilization_percentage': '0%',  # Virá do SQLite
                'ytd_availability_percentage': '0%'   # Virá do SQLite
            }

        except Exception as e:
            report_exception(e)
            trace(f"Erro ao processar dados do dashboard: {e}", color="red")
            return {}, {}, pd.DataFrame(), {}


# Função para histórico de 12 meses para "Clients Utilization"
class ClientsHistoricalProcessor:
    """
    Processador específico para dados históricos de clientes (últimos 12 meses)
    Mantém o SQLite apenas para este caso específico
    """

    def __init__(self):
        self.db_handler = get_db_handler()

    def get_last_12_months_data(self):
        """
        Obtém dados dos últimos 12 meses do SQLite
        CORREÇÃO: Aplica conversão de minutos para horas como na query original
        """
        try:
            # Verificar quantas semanas temos no SQLite
            self.db_handler.cursor.execute("""
                SELECT COUNT(DISTINCT year || '-' || week_number) as weeks_count
                FROM clients_usage
                WHERE datetime(start_date) >= datetime('now', '-12 months')
            """)
            weeks_count = self.db_handler.cursor.fetchone()[0]

            if weeks_count < 40:  # Menos de ~10 meses de dados
                trace(f"Dados insuficientes no histórico: {weeks_count} semanas. Mínimo recomendado: 40")
                return pd.DataFrame(columns=['classification', 'hours'])

            # CORREÇÃO: Usar a mesma query da imagem - converter minutos para horas
            self.db_handler.cursor.execute("""
                SELECT
                    e.new_classification as classification,
                    ROUND(SUM(c.hours) / 60.0, 2) as total_horas
                FROM clients_usage c
                INNER JOIN eja e ON c.classification = e.eja_code
                WHERE e.new_classification IS NOT NULL 
                AND e.new_classification != ''
                AND datetime(c.start_date) >= datetime('now', '-12 months')
                GROUP BY e.new_classification
                ORDER BY total_horas DESC
            """)

            rows = self.db_handler.cursor.fetchall()

            if not rows:
                return pd.DataFrame(columns=['classification', 'hours'])

            # Converter para DataFrame no formato esperado
            result_data = []
            for row in rows:
                classification = row[0]  # e.new_classification
                total_horas = row[1]     # ROUND(SUM(c.hours) / 60.0, 2)

                result_data.append({
                    'classification': classification,
                    'hours': int(total_horas)  # Agora está em horas, não minutos
                })

            df = pd.DataFrame(result_data)
            return df

        except Exception as e:
            trace(f"Erro ao obter dados históricos: {e}", color="red")
            return pd.DataFrame(columns=['classification', 'hours'])

    def needs_historical_processing(self):
        """
        Verifica se é necessário processar dados históricos
        """
        try:
            self.db_handler.cursor.execute("""
                SELECT COUNT(DISTINCT year || '-' || week_number) as weeks_count
                FROM clients_usage
                WHERE datetime(start_date) >= datetime('now', '-12 months')
            """)
            weeks_count = self.db_handler.cursor.fetchone()[0]
            return weeks_count < 40
        except Exception:
            return True


def get_simplified_processor(dashboard_df):
    """
    Função factory para obter o processador simplificado
    """
    return SimplifiedDataProcessor(dashboard_df)


def get_clients_historical_processor():
    """
    Função factory para obter o processador de histórico de clientes
    """
    return ClientsHistoricalProcessor()
