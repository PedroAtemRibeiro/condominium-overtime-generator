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
import holidays

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

def obter_feriados_mes(mes, ano):

    br = holidays.country_holidays(
        "BR",
        years=[ano]
    )

    lista = []

    for data, nome in br.items():

        if data.month == mes:

            lista.append(
                f"{data.strftime('%d/%m')} - {nome}"
            )

    return sorted(lista)


def extrair_funcionarios(pdf):

    reader = PdfReader(pdf)

    texto = ""

    for pagina in reader.pages:
        texto += (pagina.extract_text() or "") + "\n"
    fim = texto.find("Total de empregados:")

    if fim > 0:
        texto = texto[:fim]

    codigo = "0000"

    m = re.search(r"\((\d{3,4})\)", texto)

    if m:
        codigo = m.group(1).zfill(4)
    else:

        nome_arquivo = Path(pdf).stem

        m2 = re.search(r"(\d{3,4})", nome_arquivo)

        if m2:
            codigo = m2.group(1).zfill(4)

    if "Página:" in texto:
        nome_condominio = texto.split("Página:")[0].strip()
    else:
        nome_condominio = texto

    funcionarios = []

    linhas = texto.split("\n")

    cargos = [

        "ENCARREGADO DE MANUTENÇÃO PREDIAL",
        "AUX DE MANUTENÇÃO PREDIAL",

        "ENCARREGADO DE MANUTENÇÃO",
        "ENCARREGADO DE MANUTENÇAO",

        "AUXILIAR DE SERVIÇOS GERAIS",
        "AUXILIAR DE SERVIÇO GERAIS",

        "AUXILIAR DE MANUTENÇÃO",
        "AUXILIAR ADMINISTRATIVO",

        "ASSISTENTE ADMINISTRATIVO",

        "PORTEIRO NOTURNO",
        "PORTEIRO CHEFE",
        "PORTEIRO DIURNO",
        "PORTEIRO",

        "VIGIA NOTURNO",
        "VIGIA",

        "AUX DE PORTARIA",

        "FAXINEIRO",
        "SERVENTE",
        "FOLGUISTA",
        "CONCIERGE",

        "GARAGISTA",

        "GERENTE DE CONTROLE",

        "ENCARREGADO(A) DE LIMPEZA",

        "JARDINEIRO (A)",

        "ZELADOR"
    ]

    for bloco in linhas:

        registro = re.search(
            r"(\d+)\s+(.*?)\s+Mensalista\s+(\d+,\d+)",
            bloco,
            re.IGNORECASE
        )

        if not registro:
            continue

        cod = registro.group(1)

        nome_cargo = registro.group(2)

        horas = registro.group(3)

        bloco = nome_cargo


        cargo_encontrado = None

        for cargo in sorted(
            cargos,
            key=len,
            reverse=True
        ):

            pos = bloco.upper().find(
                cargo.upper()
            )

            if pos >= 0:

                nome = bloco[:pos].strip()

                if nome.startswith(cod):
                    nome = nome[len(cod):].strip()
                    
                nome = re.sub(r"^\d+\s*", "", nome)

                funcionarios.append({

                    "codigo": int(cod),

                    "nome": nome.title(),

                    "cargo": cargo.title(),

                    "escala": definir_escala(horas)

                })

                cargo_encontrado = cargo

                break

        if cargo_encontrado is None:
            continue

    funcionarios.sort(
        key=lambda x: x["codigo"]
    )

    vistos = set()

    lista_final = []

    for func in funcionarios:

        chave = (
            func["codigo"],
            func["nome"]
        )

        if chave not in vistos:

            vistos.add(chave)

            lista_final.append(func)

    return (
        codigo,
        nome_condominio,
        lista_final
    )

def gerar_pdf(pdf, pasta_saida):

    codigo, nome_condominio, funcionarios = extrair_funcionarios(pdf)



    if len(funcionarios) == 0:
        raise Exception("Nenhum funcionário encontrado")

    competencia = (
        f"{MESES[datetime.now().month]}/"
        f"{datetime.now().year}"
    )
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    feriados_mes = obter_feriados_mes(
        mes_atual,
        ano_atual
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
            40,
            40,
            40,
            40,
            40,
            40,
            40,
            40,
            160
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

    elementos.append(Spacer(1, 10))


    elementos.append(
        Paragraph(
            "<b>FERIADOS DO MÊS</b>",
            estilos["Normal"]
        )
    )

    for feriado in feriados_mes:

        elementos.append(
            Paragraph(
                feriado,
                estilos["Normal"]
            )
        )

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