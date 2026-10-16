"""Ponto de entrada: ``python -m cofre_senhas_aes256``."""

from __future__ import annotations

import sys

from .gui import main

if __name__ == "__main__":
    sys.exit(main())
