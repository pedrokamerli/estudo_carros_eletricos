"""Aqui eu centralizo a conexão do projeto com o PostgreSQL."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# Encontro a raiz do projeto para ler o arquivo .env no lugar certo.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Carrego as variáveis locais sem deixar senha exposta no código.
load_dotenv(PROJECT_ROOT / ".env")


def get_connection() -> psycopg.Connection:
    """Abro e retorno uma conexão com o banco do projeto."""
    config = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    # Paro cedo se alguma configuração necessária não estiver preenchida.
    missing_values = [key for key, value in config.items() if not value]
    if missing_values:
        raise ValueError(f"Configurações ausentes no .env: {missing_values}")

    return psycopg.connect(**config)
