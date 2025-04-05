#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para configurar a conexão com o banco de dados.
Este script permite ao usuário configurar a conexão sem editar manualmente
os arquivos de configuração.
"""

import os
import sys
import configparser
import getpass


def main():
    print("=" * 50)
    print("  Configuração de Conexão com Banco de Dados")
    print("=" * 50)

    # Verificar se o arquivo de configuração existe
    config_file = "config/db_connection.cfg"
    if not os.path.exists(config_file):
        print(f"Arquivo de configuração não encontrado: {config_file}")
        config = configparser.ConfigParser()
        config['DATABASE'] = {}
    else:
        # Ler configuração atual
        config = configparser.ConfigParser()
        config.read(config_file)

        if 'DATABASE' not in config:
            config['DATABASE'] = {}

    # Obter as configurações atuais ou definir valores padrão
    current_server = config['DATABASE'].get('SERVER', 'localhost')
    current_database = config['DATABASE'].get('DATABASE', 'dashboard_ford')
    current_driver = config['DATABASE'].get('DRIVER', 'SQL Server')
    current_trusted = config['DATABASE'].get('TRUSTED_CONNECTION', 'yes')
    current_username = config['DATABASE'].get('UID', '')

    # Solicitar novas configurações
    print("\nDigite as informações de conexão (deixe em branco para manter o valor atual):")
    server = input(f"Servidor [{current_server}]: ") or current_server
    database = input(f"Banco de dados [{current_database}]: ") or current_database
    driver = input(f"Driver ODBC [{current_driver}]: ") or current_driver

    trusted_conn = input(f"Usar autenticação do Windows (sim/não) [{current_trusted}]: ") or current_trusted
    trusted_conn = trusted_conn.lower() in ('sim', 'yes', 's', 'y', 'true')

    if not trusted_conn:
        username = input(f"Nome de usuário [{current_username}]: ") or current_username
        password = getpass.getpass("Senha: ")
    else:
        username = ''
        password = ''

    # Atualizar configuração
    config['DATABASE']['SERVER'] = server
    config['DATABASE']['DATABASE'] = database
    config['DATABASE']['DRIVER'] = driver
    config['DATABASE']['TRUSTED_CONNECTION'] = 'yes' if trusted_conn else 'no'

    if not trusted_conn and username:
        config['DATABASE']['UID'] = username
        config['DATABASE']['PWD'] = password
    elif 'UID' in config['DATABASE']:
        del config['DATABASE']['UID']
        if 'PWD' in config['DATABASE']:
            del config['DATABASE']['PWD']

    # Salvar configuração
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        config.write(f)

    print("\nConfiguração salva com sucesso!")
    print(f"Arquivo: {os.path.abspath(config_file)}")
    print("\nNota: Reinicie o container para aplicar as alterações.")


if __name__ == "__main__":
    main()
