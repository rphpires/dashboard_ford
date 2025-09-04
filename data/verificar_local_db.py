# Script para diagnosticar o mapeamento de EJAs no SQLite
# Execute este script no seu ambiente Python

import sqlite3
import os


def diagnose_eja_mapping():
    """Diagnostica o mapeamento de EJAs no banco SQLite"""

    # Caminho do banco SQLite (ajuste se necessário)
    db_path = os.path.join("data", "database.db")

    if not os.path.exists(db_path):
        print(f"ERRO: Banco SQLite não encontrado em: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        print("=" * 60)
        print("DIAGNÓSTICO DO MAPEAMENTO DE EJAs")
        print("=" * 60)

        # 1. Verificar EJAs classificados como PROGRAMS
        print("\n1. EJAs cadastrados como 'PROGRAMS':")
        cursor.execute("""
            SELECT eja_code, title 
            FROM eja 
            WHERE new_classification = 'PROGRAMS' 
            ORDER BY eja_code
        """)
        programs_ejas = cursor.fetchall()

        if programs_ejas:
            print(f"   Encontrados {len(programs_ejas)} EJAs:")
            for row in programs_ejas:
                print(f"   - {row['eja_code']}: {row['title']}")
        else:
            print("   NENHUM EJA encontrado com classificação 'PROGRAMS'")

        # 2. EJAs da consulta SQL Server que você mostrou
        sql_server_ejas = [832, 35, 36, 23, 6, 8, 12, 8, 1]  # Da sua imagem
        print(f"\n2. Verificando se os EJAs da SP ({sql_server_ejas}) estão cadastrados:")

        for eja_code in sql_server_ejas:
            cursor.execute("""
                SELECT eja_code, title, new_classification 
                FROM eja 
                WHERE eja_code = ?
            """, (eja_code,))
            result = cursor.fetchone()

            if result:
                print(f"   - EJA {eja_code}: '{result['title']}' → Classificação: '{result['new_classification']}'")
            else:
                print(f"   - EJA {eja_code}: NÃO CADASTRADO no SQLite")

        # 3. Todas as classificações disponíveis
        print("\n3. Todas as classificações cadastradas:")
        cursor.execute("""
            SELECT new_classification, COUNT(*) as quantidade 
            FROM eja 
            WHERE new_classification IS NOT NULL AND new_classification != ''
            GROUP BY new_classification 
            ORDER BY new_classification
        """)
        classifications = cursor.fetchall()

        for row in classifications:
            print(f"   - {row['new_classification']}: {row['quantidade']} EJAs")

        # 4. EJAs sem classificação
        print("\n4. EJAs sem classificação:")
        cursor.execute("""
            SELECT COUNT(*) as sem_classificacao
            FROM eja 
            WHERE new_classification IS NULL OR new_classification = ''
        """)
        no_class = cursor.fetchone()
        print(f"   - {no_class['sem_classificacao']} EJAs sem classificação")

        # 5. Verificar se algum dos EJAs da SP está em outra classificação
        print("\n5. EJAs da SP em outras classificações:")
        for eja_code in sql_server_ejas:
            cursor.execute("""
                SELECT eja_code, title, new_classification 
                FROM eja 
                WHERE eja_code = ? AND new_classification != 'PROGRAMS'
            """, (eja_code,))
            result = cursor.fetchone()

            if result:
                print(f"   - EJA {eja_code} está em '{result['new_classification']}', não em PROGRAMS")

        print("\n" + "=" * 60)
        print("DIAGNÓSTICO CONCLUÍDO")
        print("=" * 60)

        conn.close()

    except Exception as e:
        print(f"ERRO ao executar diagnóstico: {e}")


if __name__ == "__main__":
    diagnose_eja_mapping()
