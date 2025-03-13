# layouts/__init__.py
# Torna o diretório um pacote Python e exporta as funções necessárias

from layouts.header import create_header
from layouts.left_column import create_left_column
from layouts.right_column import create_right_column

__all__ = ['create_header', 'create_left_column', 'create_right_column']
