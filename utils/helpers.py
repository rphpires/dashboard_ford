def safe_time_conversion(time_str):
    """
    Converte com segurança uma string de tempo no formato HH:MM para horas decimais.
    Lida com valores vazios, None e formatos inválidos.

    Args:
        time_str: String de tempo no formato HH:MM ou valor numérico

    Returns:
        float: Valor convertido para horas decimais ou 0.0 em caso de erro
    """
    try:
        if time_str is None or time_str == "":
            return 0.0

        # Se já for um número, retornar diretamente
        if isinstance(time_str, (int, float)):
            return float(time_str)

        # Verificar se é uma string no formato HH:MM
        if isinstance(time_str, str) and ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours + (minutes / 60.0)

        # Tentar converter diretamente para float
        return float(time_str)

    except (ValueError, TypeError, AttributeError) as e:
        print(f"Erro ao converter tempo '{time_str}': {e}")
        return 0.0


# Adicione esta função ao seu arquivo utils/helpers.py ou similar

def safe_convert_to_float(value, default=0.0):
    """
    Converte um valor para float de forma segura, lidando com strings vazias e outros casos problemáticos.

    Args:
        value: O valor a ser convertido para float
        default: O valor padrão a retornar em caso de erro (padrão: 0.0)

    Returns:
        float: O valor convertido ou o valor padrão em caso de erro
    """
    if value is None:
        return default

    try:
        # Checar se é uma string vazia
        if isinstance(value, str) and value.strip() == '':
            return default

        # Tentar converter para float
        return float(value)
    except (ValueError, TypeError):
        # Em caso de erro, retornar o valor padrão
        return default


def safe_calculate_percentage(part, total, format_str=True, default="0.0%"):
    """
    Calcula uma porcentagem de forma segura, lidando com divisão por zero e valores inválidos.

    Args:
        part: O valor parcial (numerador)
        total: O valor total (denominador)
        format_str: Se True, retorna uma string formatada, caso contrário retorna um número
        default: O valor padrão a retornar em caso de erro (padrão: "0.0%")

    Returns:
        str ou float: A porcentagem calculada, formatada como string se format_str=True
    """
    try:
        # Converter valores para float de forma segura
        part_float = safe_convert_to_float(part)
        total_float = safe_convert_to_float(total)

        # Evitar divisão por zero
        if total_float <= 0:
            return default if format_str else 0.0

        # Calcular a porcentagem
        percentage = (part_float / total_float) * 100

        # Retornar o resultado formatado ou como número
        if format_str:
            return f"{percentage:.1f}%"
        else:
            return percentage

    except Exception as e:
        print(f"Erro ao calcular porcentagem: {e}")
        return default if format_str else 0.0
