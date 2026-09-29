# Projeto Portfólio

Este é o repositório do meu projeto de dados para portfólio. Nesta primeira fase, ele guarda apenas a estrutura organizada do projeto.

## Estrutura

```text
Projeto Portfólio/
├── data/
│   ├── raw/          # Dados originais, sem alterações
│   └── processed/    # Dados preparados
├── docs/             # Documentação e anotações
├── notebooks/        # Explorações e estudos
├── src/              # Código Python
├── tests/            # Testes do projeto
├── .gitignore
└── requirements.txt
```

## PyCharm

Abra esta pasta como projeto e use o interpretador localizado em `.venv`.

## Ambiente virtual

No terminal do PyCharm, ative o ambiente com:

```powershell
.\.venv\Scripts\Activate.ps1
```

As bibliotecas serão incluídas em `requirements.txt` quando forem necessárias.

## Regras do projeto

- Não enviar `.venv`, senhas ou arquivos `.env` ao GitHub.
- Manter os dados recebidos em `data/raw` sem alteração manual.
- Fazer commits pequenos e descritivos.
