"""spi/__main__.py - 让 `python -m spi` 等价于 `python -m spi.cli`"""
import sys
from .cli import main

sys.exit(main())