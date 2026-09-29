from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BRONZE_SENATRAN_PATH = PROJECT_ROOT / "data" / "bronze" / "senatran"

BRONZE_SENATRAN_PATH.mkdir(parents=True, exist_ok=True)

print("Pasta da camada Bronze criada com sucesso!")
print(f"Local: {BRONZE_SENATRAN_PATH}")