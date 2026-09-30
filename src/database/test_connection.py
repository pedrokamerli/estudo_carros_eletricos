"""Aqui eu testo se o Python consegue conversar com o PostgreSQL."""

from src.database.connection import get_connection


def main() -> None:
    """Abro uma conexão simples e mostro o banco e o usuário conectados."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            database_name, user_name = cursor.fetchone()

    print("Conexão realizada com sucesso!")
    print(f"Banco conectado: {database_name}")
    print(f"Usuário conectado: {user_name}")


if __name__ == "__main__":
    # Executo o teste apenas quando rodo este arquivo como módulo.
    main()
