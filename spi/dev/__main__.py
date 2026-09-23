"""spi/dev CLI 入口 (向后兼容, python -m spi.dev)

v26 重构后, 推荐使用 `python -m spi.cli` (dispatcher 层, 跟随 SPI_FOLDER 自动切换).
`python -m spi.dev` 仍可用, 仅显示 dev 实现的 verify 结果 (向后兼容).
"""
import sys

from .cli import _print_verify

sys.exit(_print_verify())