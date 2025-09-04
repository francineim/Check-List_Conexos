# app.py
# ------------------------------------------------------------
# Check List Parametrização (Streamlit + PDF via ReportLab)
# ------------------------------------------------------------
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Tentativa de import do ReportLab (para o PDF)
REPORTLAB_OK = True
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
except Exception:
    REPORTLAB_OK = False

# ----------------------------
# Config inicial da página
# ----------------------------
st.set_page_config(page_title="Check List Parametrização", layout="wide")
st.title("Check List Parametrização")
st.caption("Marque o que foi parametrizado e registre observações. Gere um PDF pelo botão **Relatório**.")

# ----------------------------
# Lista de tarefas (fixa)
# ----------------------------
DEFAULT_TASKS = [
    "Criar CFOP",
    "Vincular CFOP ao Tipo de Operação",
    "Criar Ordem de Faturamento",
    "Vincular Ordem de Faturamento na Pessoa",
    "Criar Classificador de Produtos",
    "Vincular Encargo de Retenção na Pessoa",
]

# ----------------------------
# Estado inicial
# ----------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"tarefa": t, "done": False, "obs": ""} for t in DEFAULT_TASKS
    ]

# ----------------------------
# Cabecalho das colunas
# ----------------------------
header_cols = st.columns([0.5, 0.2, 0.3], gap="small")
with header_cols[0]:
    st.markdown("#### Tarefa")
with header_cols[1]:
    st.markdown("#### Parametrizado?")
with header_cols[2]:
    st.markdown("#### Observação")

st.markdown("---")

# ----------------------------
# Formulário por linha
# ----------------------------
for i, item in enumerate(st.session_state.tasks):
    cols = st.columns([0.5, 0.2, 0.3], gap="small")
    with cols[0]:
        st.markdown(f"- {item['tarefa']}")
    with cols[1]:
        st.session_state.tasks[i]["done"] = st.checkbox(
            " ", value=item["done"], key=f"done_{i}", help="Marque se já foi parametrizado."
        )
    with cols[2]:
        st.session_state.tasks[i]["obs"] = st.text_area(
            label=" ", value=item["obs"], key=f"obs_{i}", height=80, placeholder="Observações, pendências, quem fez, data etc."
        )

st.markdown("---")

# ----------------------------
# Função para gerar PDF
# ----------------------------
def gerar_pdf(tasks_data: pd.DataFrame) -> bytes:
    """
    Gera um PDF (bytes) com título, data/hora e tabela das tarefas.
    Requer ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=1.8*cm,
        bottomMargin=1.8*cm,
        title="Check List Parametrização"
    )

    styles = getSampleStyleSheet()
    titulo = styles["Title"]
    normal = styles["BodyText"]

    story = []
    story.append(Paragraph("Check List Parametrização", titulo))
    story.append(Spacer(1, 6))
    story.append(Paragraph(datetime.now().strftime("Gerado em %d/%m/%Y %H:%M:%S"), normal))
    story.append(Spacer(1, 12))

    # Monta tabela
    data = [["Tarefa", "Status", "Observação"]]
    for _, row in tasks_data.iterrows():
        data.append([
            row["Tarefa"],
            row["Status"],
            row["Observação"] if row["Observação"] else "-"
        ])

    table = Table(data, colWidths=[7.5*cm, 3.0*cm, 6.0*cm])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (1,1), (1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))

    story.append(table)
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# ----------------------------
# Monta DataFrame atual
# ----------------------------
df = pd.DataFrame([
    {
        "Tarefa": item["tarefa"],
        "Status": "Parametrizado" if item["done"] else "Pendente",
        "Observação": item["obs"]
    }
    for item in st.session_state.tasks
])

with st.expander("Visualizar como tabela (prévia)", expanded=False):
    st.dataframe(df, use_container_width=True)

# ----------------------------
# Botões de ação
# ----------------------------
btn_cols = st.columns([0.25, 0.25, 0.5])
with btn_cols[0]:
    gerar = st.button("Relatório", type="primary")
with btn_cols[1]:
    limpar = st.button("Limpar observações/flags")

if limpar:
    for i in range(len(st.session_state.tasks)):
        st.session_state.tasks[i]["done"] = False
        st.session_state.tasks[i]["obs"] = ""
        st.session_state[f"done_{i}"] = False
        st.session_state[f"obs_{i}"] = ""
    st.success("Checklist limpo.")

if gerar:
    if not REPORTLAB_OK:
        st.error(
            "Biblioteca **reportlab** não encontrada. Instale com `pip install reportlab` e tente novamente."
        )
    else:
        pdf_content = gerar_pdf(df)
        file_name = f"checklist_parametrizacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            label="⬇️ Baixar PDF do Relatório",
            data=pdf_content,
            file_name=file_name,
            mime="application/pdf",
        )
        st.success("Relatório gerado com sucesso.")

# Rodapé
st.markdown("---")
st.caption("Dica: use o botão **Limpar** antes de iniciar um novo ciclo de parametrização.")
