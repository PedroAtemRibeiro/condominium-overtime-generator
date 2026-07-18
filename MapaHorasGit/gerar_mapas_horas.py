from tkinter import Tk, filedialog, messagebox
from pathlib import Path
from datetime import datetime
from pypdf import PdfReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, landscape
import re

MESES = {
    1: "JANEIRO",
    2: "FEVEREIRO",
    3: "MARÇO",
    4: "ABRIL",
    5: "MAIO",
    6: "JUNHO",
    7: "JULHO",
    8: "AGOSTO",
    9: "SETEMBRO",
    10: "OUTUBRO",
    11: "NOVEMBRO",
    12: "DEZEMBRO"
}


def definir_escala(horas):

    try:
        horas = float(str(horas).replace(",", "."))
    except:
        return "Horista"

    if abs(horas - 180) < 0.01:
        return "12x36"

    if abs(horas - 220) < 0.01:
        return "06x01"

    return "Horista"


def extrair_funcionarios(pdf):

    texto = ""

    reader = PdfReader(pdf)

    for pagina in reader.pages:
        texto += (pagina.extract_text() or "") + " "

    codigo = "0000"

    
    m = re.search(r"\((\d{4})\)", texto)

    if m:
        codigo = m.group(1)
    else:

        nome_arquivo = Path(pdf).stem

        m2 = re.search(r"(\d{4})", nome_arquivo)

        if m2:
            codigo = m2.group(1)


    nome_condominio = texto.split("Página:")[0].strip()

    funcionarios = []

    padrao = re.compile(
        r"(\d+)\s+(.+?)Mensalista\s+(\d+,\d+)",
        re.IGNORECASE
    )

    for registro in padrao.finditer(texto):

        print("=" * 50)
        print(registro.group(2))

        cod = registro.group(1)
        bloco = registro.group(2).strip()
        horas = registro.group(3)
        
        for cargo_fix in [

            "PORTEIRO NOTURNO",
            "PORTEIRO CHEFE",
            "PORTEIRO DIURNO",
            "PORTEIRO",

            "VIGIA NOTURNO",
            "VIGIA",

            "ZELADOR",
            "FAXINEIRO",
            "SERVENTE",
            "FOLGUISTA",
            "CONCIERGE",

            "AUX DE PORTARIA",
            "AUXILIAR DE MANUTENÇÃO",
            "AUXILIAR DE SERVIÇO GERAIS",
            "AUXILIAR DE SERVIÇOS GERAIS",

            "ASSISTENTE ADMINISTRATIVO",

            "ENCARREGADO DE MANUTENÇÃO",
            "ENCARREGADO DE MANUTENÇAO",
            "ENCARREGADO(A) DE LIMPEZA",

            "GARAGISTA",
            "GERENTE DE CONTROLE",
            "JARDINEIRO (A)"

        ]:

            bloco = re.sub(
                rf"([A-ZÀ-Ú])({re.escape(cargo_fix)})",
                r"\1 \2",
                bloco,
                flags=re.IGNORECASE
            )

        partes = bloco.split()

        if len(partes) < 2:
            continue

        cargo_encontrado = ""

        palavras_cargo = [
            "PORTEIRO",
            "NOTURNO",         
            "DIURNO",
            "GERENTE",
            "CONTROLE",
            "GARAGISTA",
            "SERVIÇOS",
            "SERVIÇO",
            "GERAIS",
            "JARDINEIRO",
            "LIMPEZA",
            "CHEFE",
            "VIGIA",
            "ZELADOR",
            "FAXINEIRO",
            "SERVENTE",
            "FOLGUISTA",
            "AUX",
            "AUXILIAR",
            "ENCARREGADO",
            "ASSISTENTE",
            "ADMINISTRATIVO",
            "MANUTENÇÃO",
            "MANUTENÇAO",
            "PORTARIA",
	        "CONCIERGE",
            "PREDIAL"
        ]

        posicao_cargo = None

        for i, palavra in enumerate(partes):

            if palavra.upper() in palavras_cargo:

                posicao_cargo = i
                break

        if posicao_cargo is None:
            continue

        nome = " ".join(partes[:posicao_cargo])

        cargo = " ".join(partes[posicao_cargo:])

        funcionarios.append({
            "codigo": int(cod),
            "nome": nome.title(),
            "cargo": cargo.title(),
            "escala": definir_escala(horas)
        })
        
        print("ADICIONADO:")
        print(nome)
        print("TOTAL ATUAL:", len(funcionarios))


    funcionarios.sort(
        key=lambda x: x["codigo"]
    )
    
    if len(funcionarios) == 0:

        print("SEM FUNCIONARIOS:")
        print(pdf)
    
        print("ANTES DO RETURN:")
        print("CONDOMINIO:", codigo)
        print("FUNCIONARIOS:", len(funcionarios))
    
    	
    return codigo, nome_condominio, funcionarios

def gerar_pdf(pdf, pasta_saida):

    codigo, nome_condominio, funcionarios = extrair_funcionarios(pdf)

    
    print("RECEBIDO NA GERACAO:")
    print(codigo)
    print("TOTAL:", len(funcionarios))


    if len(funcionarios) == 0:
        raise Exception("Nenhum funcionário encontrado")

    competencia = (
        f"{MESES[datetime.now().month]}/"
        f"{datetime.now().year}"
    )

    arquivo_saida = (
        Path(pasta_saida)
        / f"{codigo}_MapaHoras.pdf"
    )

    doc = SimpleDocTemplate(
        str(arquivo_saida),
        pagesize=landscape(A4),
        leftMargin=10,
        rightMargin=10,
        topMargin=10,
        bottomMargin=10
    )

    estilos = getSampleStyleSheet()

    elementos = []

    elementos.append(
        Paragraph(
            f"<b>{nome_condominio}</b>",
            estilos["Title"]
        )
    )

    elementos.append(
        Paragraph(
            f"Código Condomínio: {codigo}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"Mês de Competência: {competencia}",
            estilos["Normal"]
        )
    )

    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            "PLANILHA DE PONTO DOS EMPREGADOS DO MÊS",
            estilos["Heading2"]
        )
    )

    elementos.append(Spacer(1, 10))

    dados = [[
        "Funcionário",
        "Função",
        "HE\nFixa",
        "HE\nArt.71",
        "Adic.\nNoturno",
        "Folga\n100%",
        "Feriado\n100%",
        "HE\n60%",
        "Faltas",
        "Gratif.",
        "Observações"
    ]]
    
    print("CONDOMINIO:", codigo)
    print("TOTAL FUNCIONARIOS:", len(funcionarios))


    for f in funcionarios:

        dados.append([
            f"{f['codigo']} - {f['nome']}",
            f"{f['cargo']} - {f['escala']}",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ])

    tabela = Table(
        dados,
        repeatRows=1,
        colWidths=[
            170,
            130,
            45,
            50,
            55,
            55,
            55,
            45,
            40,
            50,
            85
        ]
    )

    tabela.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]))

    elementos.append(tabela)

    elementos.append(Spacer(1, 20))

    assinaturas = Table(
        [
            [
                "________________________________",
                "________________________________"
            ],
            [
                "Zelador",
                "Síndico(a)"
            ]
        ],
        colWidths=[300, 300]
    )

    elementos.append(assinaturas)

    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            "OBS: Por favor devolver até no máximo dia 18 de cada mês "
            "para a confecção da folha de pagamento. Caso isso não aconteça, "
            "repetiremos os mesmos valores da folha anterior.",
            estilos["Normal"]
        )
    )

    doc.build(elementos)


root = Tk()
root.withdraw()

pasta_cadastros = filedialog.askdirectory(
    title="Selecione a pasta dos PDFs de cadastro"
)

if pasta_cadastros:

    pasta_saida = (
        Path(pasta_cadastros)
        / "Mapas_Gerados"
    )

    pasta_saida.mkdir(exist_ok=True)

    arquivo_erros = (
        Path(pasta_saida)
        / "erros.txt"
    )

    if arquivo_erros.exists():
        arquivo_erros.unlink()

    total_ok = 0
    total_erro = 0


    arquivos = list(Path(pasta_cadastros).glob("*.pdf"))

    print(f"PDFs encontrados: {len(arquivos)}")

    for pdf in arquivos:


        try:

            gerar_pdf(
                pdf,
                pasta_saida
            )

            total_ok += 1

        except Exception as erro:

            total_erro += 1

            with open(
                arquivo_erros,
                "a",
                encoding="utf-8"
            ) as f:

                f.write(
                    f"{pdf.name} -> {str(erro)}\n"
                )

    messagebox.showinfo(
        "Concluído",
        f"Mapas gerados: {total_ok}\n"
        f"Com erro: {total_erro}\n\n"
        f"Verifique o arquivo erros.txt caso existam erros."
    )