from pathlib import Path


BUILTINS_ROOT = Path(__file__).parent


def builtin_path(*parts: str) -> Path:
    return BUILTINS_ROOT.joinpath(*parts)


__all__ = ["BUILTINS_ROOT", "builtin_path"]
