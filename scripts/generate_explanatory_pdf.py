"""Gero meu relatório de entrega a partir dos resultados realmente exportados."""

import csv
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/portfolio"
OUTPUT = ROOT / "output/pdf/Relatorio_Entrega_Projeto_EV.pdf"


def read(name):
    with (DATA / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    models = read("abve_publico_modelo_gold.csv")
    cities = read("abve_publico_municipio_gold.csv")
    catalog = read("inmetro_versoes_eletrificadas.csv")
    quarantine = read("inmetro_quarentena.csv")
    coverage = read("ml_intervalos_cobertura.csv")
    def br_count(value):
        return f"{value:,}".replace(",", ".")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleEV", fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=colors.HexColor("#143D52"), spaceAfter=20))
    styles.add(ParagraphStyle(name="SectionEV", fontName="Helvetica-Bold", fontSize=17, leading=22, textColor=colors.HexColor("#143D52"), spaceAfter=15))
    styles.add(ParagraphStyle(name="BodyEV", fontSize=10.5, leading=15, spaceAfter=11))
    styles.add(ParagraphStyle(name="SmallEV", fontSize=8.5, leading=12, spaceAfter=8))
    styles.add(ParagraphStyle(name="CellEV", fontSize=9, leading=12))
    story = []
    def p(text, style="BodyEV"):
        story.append(Paragraph(text, styles[style]))
    def section(title):
        p(title, "SectionEV")
    def table(rows, widths):
        cells = [[Paragraph(escape(str(v)), styles["CellEV"]) for v in row] for row in rows]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DFEBEF")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 8),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 8), ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#CED9DE"))]))
        story.extend([t, Spacer(1, 15)])
    def next_page():
        story.append(PageBreak())

    p("O que foi feito no meu<br/>projeto de veículos elétricos", "TitleEV")
    p("Entrega técnica e explicação didática | 01/10/2026", "SmallEV")
    p("Pedro, nesta entrega ampliei as fontes reais do projeto, automatizei a coleta do painel público de vendas ABVE e testei a incerteza das previsões. O período observado continua sendo janeiro/2024 a agosto/2026. Não inventei meses nem usei os CSVs sem fonte confirmada como dados oficiais.")
    table([["Frente", "Resultado desta execução"],
           ["Histórico ABVE", f"32 meses; {br_count(len(models))} linhas por marca/modelo/tecnologia e {br_count(len(cities))} por município/tecnologia."],
           ["Captura automatizada", "Respostas públicas guardadas em Bronze; três recortes conciliados por mês e tecnologia."],
           ["Inmetro", f"{br_count(len(catalog))} linhas de versões nos ciclos 2024, 2025 e 2026. {len(quarantine)} linhas problemáticas em quarentena; ciclo afetado é parcial."],
           ["Incerteza do ML", "Sete alvos avaliados; quatro das cinco regiões ficaram abaixo da cobertura nominal. Sem aprovação operacional."],
           ["Visualização", "Streamlit ampliado com novas bases e cobertura dos intervalos. Power BI continua sendo sua entrega visual."]], [115, 390])
    p("<b>O que significa pronto?</b> Os dados extraídos e aceitos têm regras de validação e saídas consultáveis. Isso não significa que todas as aplicações de ML já sejam confiáveis nem que cada versão Inmetro já esteja ligada a um modelo ABVE.")

    next_page()
    section("1. Como as peças se conectam")
    p("Pense no projeto como uma cozinha. Bronze é a despensa com os ingredientes originais. Silver é a bancada onde confiro, separo e padronizo. Gold é o prato organizado para a análise. Streamlit e Power BI são as formas de apresentar esse resultado.")
    table([["Camada", "O que preservo e por quê"],
           ["Bronze", "PDFs Inmetro, metadados e respostas JSON públicas ABVE. Preciso poder voltar à origem quando um número parecer estranho."],
           ["Silver", "Linhas decodificadas, catálogos em Parquet e validações. Não trato um campo vazio como zero nem misturo unidade e tecnologia."],
           ["Gold", "Agregados validados no PostgreSQL, com identificadores, fonte e período. São as tabelas que você consulta e leva ao Power BI."],
           ["Exports", "CSVs compartilháveis em data/portfolio. O Streamlit lê esses arquivos sem acessar sua senha do banco."]], [110, 395])
    p("<b>Estoque não é fluxo.</b> Frota SENATRAN é a quantidade existente em uma fotografia mensal. Emplacamentos ABVE são novos registros no mês. Somar as frotas de janeiro e fevereiro contaria muitos carros duas vezes. Somar emplacamentos mensais, dentro da mesma definição, produz um acumulado do período.")
    p("<b>Granularidade é o significado de uma linha.</b> Na ABVE de modelos, uma linha representa mês + marca + modelo + tecnologia. Na municipal, representa mês + UF + município + tecnologia. As tabelas não revelam qual modelo foi vendido em cada município. Cruzá-las diretamente poderia multiplicar as quantidades.")
    p("Os comentários dos módulos novos foram escritos em primeira pessoa: explicam minha decisão e o motivo da regra, não apenas repetem o nome do comando.")

    next_page()
    section("2. O histórico ABVE que consegui automatizar")
    p("O coletor encontra o relatório incorporado na página pública ABVE, identifica o endereço usado pelo próprio painel e pede agregados mensais dos campos exibidos. Não utiliza senha, conta privada ou dados de consumidores. Esse acesso é do painel publicado, não uma API com contrato de estabilidade.")
    p("A resposta vem compactada: alguns textos aparecem como códigos de dicionário, outros como texto literal; há máscaras indicando repetição e nulos. O decodificador reconstrói isso e recusa sinais de truncamento. Modelo e município são consultados mês a mês para limitar o tamanho de cada resposta.")
    p("<b>Conferência feita:</b> os três recortes somam exatamente o mesmo resultado em cada mês e tecnologia. O recorte inclui MHEV. Em agosto/2026, o total com MHEV é 64.055, enquanto BEV + PHEV + HEV + HEV FLEX somam 57.386. São definições diferentes, não erro de soma.")
    p("Para comparações mais consistentes ao longo dos 32 meses, começo por BEV e PHEV separadamente. MHEV e mudanças da classificação continuam visíveis, sem uma conversão inventada para HEV.")
    p("Comparei 64 observações BEV/PHEV com a série anterior. PHEV em julho/2024 aparece como 6.660 no painel atual e 6.659 na série anterior. A diferença foi registrada em abve_publico_conciliacao_plugin.csv; a série antiga e seu treino não foram silenciosamente substituídos.")
    p("Localidades sem identificação foram preservadas. Não distribuí suas quantidades entre cidades conhecidas e não preenchi combinações ausentes com zero. A conciliação interna comprova consistência dos recortes, não que o painel seja um censo sem erros.")
    p('Fonte: <link href="https://abve.org.br/abve-data/bi-geral/" color="#236D84">ABVE - painel público de vendas</link>.', "SmallEV")

    next_page()
    section("3. Inmetro: o que acrescenta e o que não resolve")
    p("Baixei os PDFs oficiais dos ciclos 2024, 2025 e 2026. Cada arquivo tem endereço da fonte, data de captura e hash SHA-256: uma impressão digital que me permite detectar alterações no original.")
    by_year = [["Ciclo", "Linhas extraídas", "Estado"]]
    for year in (2024, 2025, 2026):
        rows = [r for r in catalog if int(r["ano_ciclo"]) == year]
        by_year.append([year, len(rows), "Parcial, com quarentena" if rows[0]["status_cobertura_ciclo"] == "parcial_com_quarentena" else "Extração sem erro detectado"])
    table(by_year, [60, 115, 330])
    p("O catálogo acrescenta marca, modelo, versão, propulsão original, combustível, consumo energético em MJ/km e autonomia elétrica de ensaio em km. Versão ausente continua nula. O rótulo híbrido do catálogo não é convertido automaticamente em uma categoria mais específica que a fonte não comprovou.")
    p("Os layouts têm 28 ou 33 colunas, por isso uso posições revisadas por layout. Uma linha fundida de duas versões Volvo foi separada somente quando a repetição de marca/modelo e as colunas permitiam identificar duas linhas físicas. Sobreposições ambíguas, como textos misturados na página 7 de 2026, foram registradas em quarentena.")
    p("<b>Limites importantes:</b> o ano do ciclo não é prova de que aquele catálogo estava disponível em cada mês histórico. Não utilizo esse snapshot como atributo passado do treino. Autonomia de laboratório não é autonomia real no trânsito; catálogo não informa vendas, bateria usada, manutenção ou depreciação.")
    p("Ainda falta revisar as associações entre nomes ABVE e versões Inmetro. Um modelo pode ter várias versões e motorizações. Não fiz um join aproximado que pudesse atribuir autonomia de uma versão a todas as vendas daquele modelo.")
    p('Fonte: <link href="https://www.gov.br/inmetro/pt-br/assuntos/regulamentacao/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular" color="#236D84">Inmetro - tabelas PBE Veicular</link>.', "SmallEV")

    next_page()
    section("4. Por que testei faixas, não só um número")
    p("Uma previsão pontual de 100 carros pode esconder uma grande margem de erro. O intervalo tenta mostrar uma faixa plausível. Antes de confiar nessa faixa, verifico quantas observações reais ficaram dentro dela, sem usar o resultado do teste para escolher ou calibrar o método.")
    p("O protocolo novo é de <b>um mês à frente</b>: escolho o método usando julho a setembro/2025; calibro erros relativos em outubro/2025 a janeiro/2026; avalio fevereiro a agosto/2026. São três meses de seleção, quatro de calibração e sete de teste. Essa escolha pode diferir do experimento anterior de três horizontes.")
    table([["Alvo", "Cobertura observada", "Leitura"]] + [[r["alvo"], f"{float(r['cobertura_teste_percentual']):.1f}%".replace(".", ","), "Insuficiente" if float(r["cobertura_teste_percentual"]) < 80 else "Amostra pequena; não aprovado"] for r in coverage], [130, 135, 240])
    p("O nível nominal é 80%. Com quatro erros de calibração, o quantil finito usado é o maior erro dessa amostra; 90% exigiria mais observações. As quatro regiões abaixo de 80% mostram que a faixa não generalizou bem. Mesmo 100% em sete testes não comprova uma garantia futura.")
    p("As séries têm dependência temporal, revisões e poucas observações. O teste é retrospectivo, não um experimento prospectivo intocado. Os intervalos são experimentais; suas larguras também precisam ser consideradas. Não recomendo decisões comerciais apoiadas apenas nessas previsões.")
    p("As sete projeções de setembro/2026 são identificadas como projeções de um mês, não observações coletadas nem ampliação do recorte histórico. Não há intervalo validado para dois ou três meses nesta entrega.")

    next_page()
    section("5. Onde consultar e como continuar")
    table([["Tabelas Gold no PostgreSQL", "Uso correto"],
           ["abve_publico_tecnologia", "Evolução mensal por tecnologia; filtrar explicitamente MHEV."],
           ["abve_publico_modelo", "Marcas e modelos por mês/tecnologia; não misturar com frota."],
           ["abve_publico_municipio", "Emplacamentos por localidade/tecnologia; preservar desconhecidos."],
           ["inmetro_versoes_eletrificadas", "Explorar versões e ensaio; verificar cobertura parcial do ciclo."],
           ["ml_intervalos_detalhe / cobertura / projecoes", "Auditar erros e faixas experimentais; sem garantia operacional."]], [235, 270])
    p("No Streamlit, abra <b>Novas bases ABVE e Inmetro</b>. Em <b>ML e previsões</b>, consulte a cobertura dos intervalos. Abrir a tela não baixa dados nem treina modelos: ela só lê os exports já produzidos.")
    p("<b>Atualização:</b> python -m src.run_project executa a sequência e para no primeiro erro. Os coletores reaproveitam arquivos para reprodução. Para recapturar o painel ABVE: python -m src.ingestion.capture_abve_aggregates --refresh; depois execute src.transformation.abve_public_to_silver e src.database.load_public_enrichment com python -m.")
    p("<b>Validação desta entrega:</b> cinco testes unitários novos passaram. A descoberta unittest executou 52 casos: 48 passaram e quatro testes de banco ficaram inicialmente ignorados; os quatro passaram em execução local separada. Conferi também as contagens das novas tabelas e a conciliação municipal/modelos no PostgreSQL. Executei as etapas novas; não repeti toda a pipeline antiga nesta entrega. Isso não aprova o ML nem as medidas em um PBIX.")
    p("<b>O que ainda merece trabalho:</b> associação revisada ABVE/Inmetro por versão; revisão das linhas em quarentena; avaliação prospectiva com mais meses; captura automática da recarga ABVE e cuidados de licença antes de redistribuir os dados em escala. Não existem dados suficientes aqui para falhas de bateria, probabilidade individual de compra ou autonomia real.")
    p("Sua próxima entrega principal é o Power BI: conectar o banco, criar páginas e conferir totais de cada visual. O esquema dimensional anterior continua disponível. As novas tabelas de emplacamentos são fatos separados; a integração delas no modelo Power BI deve respeitar essa granularidade.")

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#CAD8DE"))
        canvas.line(45, 43, A4[0] - 45, 43)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526975"))
        canvas.drawString(45, 29, "Projeto de portfólio | Pedro Kamerli | Fontes públicas e limitações preservadas")
        canvas.drawRightString(A4[0] - 45, 29, str(doc.page))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=45, leftMargin=45, topMargin=48, bottomMargin=60,
                            title="Entrega e explicação do projeto EV Brasil", author="Pedro Kamerli")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
