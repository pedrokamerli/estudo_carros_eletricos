from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

FILE_NAME = "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
FILE_PATH = BRONZE_SENATRAN_PATH / FILE_NAME


def validate_source_file() -> None:
    if not FILE_PATH.exists():
        print("Arquivo não encontrado.")
        print(f"Esperado em: {FILE_PATH}")
        return

    file_size_mb = FILE_PATH.stat().st_size / 1024 / 1024

    print("Arquivo da SENATRAN encontrado com sucesso!")
    print(f"Local: {FILE_PATH}")
    print(f"Tamanho: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    validate_source_file()