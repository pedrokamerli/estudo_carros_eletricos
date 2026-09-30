"""Este é o ponto de entrada para executar minha primeira pipeline local."""

import logging

from src.transformation.bronze_to_silver import transform_bronze_to_silver


def main() -> None:
    # Configuro como os logs vão aparecer no terminal antes de iniciar a pipeline.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    # Executo a transformação e guardo o resultado para mostrar um resumo final.
    silver_dataframe = transform_bronze_to_silver()
    # Somo a coluna já padronizada na Silver para confirmar o total processado.
    total_vehicles = silver_dataframe["quantidade_veiculos"].sum()

    print("Pipeline concluída com sucesso.")
    print(f"Veículos eletrificados na Silver: {total_vehicles:,}")


if __name__ == "__main__":
    # Só executo a pipeline quando este arquivo é chamado diretamente pelo Python.
    main()
