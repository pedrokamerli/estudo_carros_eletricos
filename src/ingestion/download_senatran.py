from pathlib import Path

# Descubro a raiz do projeto sem escrever o endereço completo do computador.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Defino onde o arquivo Bronze da SENATRAN deve ficar guardado.
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

# Mantenho o nome original da fonte para facilitar a rastreabilidade do dado.
FILE_NAME = "D_Frota_por_UF_Municipio_COMBUSTIVEL_Dezembro_2025.xlsx"
FILE_PATH = BRONZE_SENATRAN_PATH / FILE_NAME


def validate_source_file() -> None:
    # Antes de analisar, confirmo que o arquivo realmente foi salvo na camada Bronze.
    if not FILE_PATH.exists():
        print("Arquivo não encontrado.")
        print(f"Esperado em: {FILE_PATH}")
        return

    # Converto o tamanho de bytes para megabytes, que é mais fácil de conferir.
    file_size_mb = FILE_PATH.stat().st_size / 1024 / 1024

    print("Arquivo da SENATRAN encontrado com sucesso!")
    print(f"Local: {FILE_PATH}")
    print(f"Tamanho: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    # Executo a validação somente quando rodo este arquivo diretamente.
    validate_source_file()
