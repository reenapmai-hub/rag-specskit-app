"""Utility to load .env into process environment and run pytest for given files.

Usage:
    python scripts/run_pytest_with_env.py tests/test_chroma_connection.py
"""
import os
import sys

def load_env(path='.env'):
    if not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip()
            os.environ.setdefault(k, v)

if __name__ == '__main__':
    load_env('.env')
    import pytest
    args = sys.argv[1:] if len(sys.argv) > 1 else ['-q']
    sys.exit(pytest.main(args))
