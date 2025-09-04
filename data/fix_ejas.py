# Script para cadastrar os EJAs faltantes no SQLite
import sqlite3
import os

def insert_missing_programs_ejas():
    """Cadastra os EJAs faltantes como PROGRAMS"""
    
    # EJAs da SP que precisam ser cadastrados como PROGRAMS
    missing_ejas = [
        (832, "SA Indirect And Fixed Expenses"),
        (35, "CX743MCA2 PL8 Brazil"),
        (36, "SA Build Ups PL7 PL8 Homologation"),
        (23, "Connectivity"),
        (6, "2024.75MY V363 ICA3 SA SKD"),
        (8, "SA - Legacy Products"),
        (12, "P703 25MY ICA2 Bundle"),
        (1, "NA - Feature Development")
    ]
    
    db_path = os.path.join("data", "database.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Cadastrando EJAs faltantes como PROGRAMS...")
        
        for eja_code, title in missing_ejas:
            try:
                cursor.execute("""
                    INSERT INTO eja (eja_code, title, new_classification, classification)
                    VALUES (?, ?, 'PROGRAMS', 'PROGRAMS')
                """, (eja_code, title))
                print(f"✓ EJA {eja_code}: {title}")
            except sqlite3.IntegrityError:
                print(f"✗ EJA {eja_code} já existe")
        
        conn.commit()
        print(f"\n{len(missing_ejas)} EJAs processados com sucesso!")
        
        # Verificar se foram inseridos
        cursor.execute("""
            SELECT COUNT(*) FROM eja 
            WHERE new_classification = 'PROGRAMS' AND eja_code IN (832, 35, 36, 23, 6, 8, 12, 1)
        """)
        count = cursor.fetchone()[0]
        print(f"Total de EJAs PROGRAMS com os códigos da SP: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    insert_missing_programs_ejas()