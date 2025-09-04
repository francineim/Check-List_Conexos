# check_list.py
# ------------------------------------------------------------
# Check List Parametrização (Streamlit + PDF via ReportLab)
# ------------------------------------------------------------
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, date

# Tentativa de import do ReportLab (para o PDF)
REPORTLAB_OK = True
try:
    from reportlab.lib.pagesizes import A4, portrait  # <- retrato
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
except Exception:
    REPORTLAB_OK = False

st.set_page_config(page_title="Check List Parametrização", layout="wide")
st.title("Check List Parametrização")

# Aviso/objetivo
st.info(
    "O objetivo desse checklist é auxiliar nas parametrizações dos sistemas, ajudando a garantir que o sistema "
    "não tenha redundâncias, eliminar retrabalho e atendimentos desnecessários."
)

# --------- Estrutura das seções e tarefas ---------
SECTIONS = [
    {
        "sec": "1. Validações antes da parametrização",
        "tasks": [
            "Consultas: já existe algo configurado para outro cliente?",
            "Classificadores: já existe para a mesma NCM ou tipo de operação?",
        ],
    },
    {
        "sec": "2. Usar ferramentas corretas e duplicidades",
        "tasks": [
            "Foi consultada a planilha ajustada pelo Izepe para prever conflitos",
            "Foi feita conferência para evitar criar parâmetros com a mesma operação ou UF's?",
        ],
    },
    {
        "sec": "3. Parametrização de CFOP",
        "tasks": [
            "CFOP movimenta estoque?",
            "Foram vinculadas as variáveis de observações de nota fiscais?",
            "CFOP será usado em pedido de venda, foi vinculado o plano financeiro?",
        ],
    },
    {
        "sec": "4. Gerais",
        "tasks": [
            "Criar CFOP",
            "Vincular CFOP ao Tipo de Operação",
            "Criar Ordem de Faturamento",
            "Vincular Ordem de Faturamento na Pessoa",
            "Criar Classificador de Produtos",
            "Vincular Encargo de Retenção na Pessoa",
        ],
    },
]

# Inicializa estado
def build_items():
    items = []
    for s_idx, sec in enumerate(SECTIONS):
        for t_idx, t in enumerate(sec["tasks"]):
            items.append(
                {
                    "section": sec["sec"],
                    "task": t,
                    "done": False,
                    "obs": "",
                    "responsavel": "",
                    "date": None,  # datetime.date
                    "key_done": f"done_{s_idx}_{t_idx}",
                    "key_obs": f"obs_{s_idx}_{t_idx}",
                    "key_resp": f"resp_{s_idx}_{t_idx}",
                    "key_date": f"date_{s_idx}_{t_idx}",
                }
            )
    return items

if "items" not in st.session_state:
    st.session_state["items"] = build_items()

# Cabeçalho
hdr = st.columns([0.35, 0.1, 0.18, 0.17, 0.20], gap="small")
with hdr[0]:
    st.markdown("#### Tarefa")
with hdr[1]:
    st.markdown("#### Feito?")
with hdr[2]:
    st.markdown("#### Responsável")
with hdr[3]:
    st.markdown("#### Data")
with hdr[4]:
    st.markdown("#### Observação")
st.markdown("---")

# Renderização agrupada por seção
for sec in SECTIONS:
    st.markdown(f"### {sec['sec']}")
    for itm in [x for x in st.session_state["items"] if x["section"] == sec["sec"]]:
        cols = st.columns([0.35, 0.1, 0.18, 0.17, 0.20], gap="small")

        # Tarefa (verde quando concluída)
        with cols[0]:
            if st.session_state.get(itm["key_done"], itm["done"]):
                st.markdown(f"<span style='color:#1a7f37'>✅ {itm['task']}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"- {itm['task']}")

        # Checkbox "feito"
        with cols[1]:
            new_done = st.checkbox(
                " ", value=st.session_state.get(itm["key_done"], itm["done"]),
                key=itm["key_done"], help="Marque se já foi parametrizado."
            )
            itm["done"] = new_done

        # Responsável
        with cols[2]:
            new_resp = st.text_input(
                label=" ", value=st.session_state.get(itm["key_resp"], itm["responsavel"]),
                key=itm["key_resp"], placeholder="Nome ou equipe"
            )
            itm["responsavel"] = new_resp

        # Data
        with cols[3]:
            if itm.get("date"):
                new_date = st.date_input(" ", value=itm["date"], key=itm["key_date"])
            else:
                new_date = st.date_input(" ", key=itm["key_date"])
            if isinstance(new_date, date):
                itm["date"] = new_date

        # Observação
        with cols[4]:
            new_obs = st.text_area(
                label=" ", value=st.session_state.get(itm["key_obs"], itm["obs"]),
                key=itm["key_obs"], height=70, placeholder="Observações, pendências..."
            )
            itm["obs"] = new_obs

    st.markdown("---")

# Monta DataFrame para prévia/relatório
def fmt_date(d):
    return d.strftime("%d/%m/%Y") if isinstance(d, date) else ""

df = pd.DataFrame(
    [
        {
            "Seção": itm["section"],
            "Tarefa": itm["task"],
            "Status": "Parametrizado" if itm["done"] else "Pendente",
            "Responsável": itm["responsavel"],
            "Data": fmt_date(itm["date"]),
            "Observação": itm["obs"],
        }
        for itm in st.session_state["items"]
    ]
)

with st.expander("Prévia em tabela", expanded=False):
    def styler(row):
        color = "background-color: #e9f7ef" if row["Status"] == "Parametrizado" else ""
        return [color] * len(row)

    st.dataframe(
        df.style.apply(styler, axis=1),
        use_container_width=True,
        hide_index=True
    )

# --------- PDF (A4 retrato) ---------
def gerar_pdf(df_: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=portrait(A4),  # <- garante A4 retrato
        leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.8*cm, bottomMargin=1.8*cm,
        title="Check List Parametrização"
    )
    styles = getSampleStyleSheet()
    titulo = styles["Title"]
    normal = styles["BodyText"]

    story = []
    story.append(Paragraph("Check List Parametrização", titulo))
    story.append(Spacer(1, 6))
    story.append(Paragraph(datetime.now().strftime("Gerado em %d/%m/%Y %H:%M:%S"), normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "O objetivo desse checklist é auxiliar nas parametrizações dos sistemas, ajudando a garantir que o sistema "
        "não tenha redundâncias, eliminar retrabalho e atendimentos desnecessários.", normal
    ))
    story.append(Spacer(1, 14))

    data = [["Seção", "Tarefa", "Status", "Responsável", "Data", "Observação"]]
    for _, r in df_.iterrows():
        data.append([
            r["Seção"],
            r["Tarefa"],
            r["Status"],
            r["Responsável"] if r["Responsável"] else "-",
            r["Data"] if r["Data"] else "-",
            r["Observação"] if r["Observação"] else "-",
        ])

    table = Table(data, colWidths=[3.0*cm, 7.0*cm, 2.3*cm, 3.0*cm, 2.0*cm, 3.0*cm])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTSIZE", (0,0), (-1,-1), 8.6),
        ("ALIGN", (2,1), (2,-1), "CENTER"),
        ("ALIGN", (4,1), (4,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))

    story.append(table)
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# Botões
c1, c2, _ = st.columns([0.22, 0.22, 0.56])
with c1:
    gerar = st.button("Relatório", type="primary")
with c2:
    limpar = st.button("Limpar observações/flags")

if limpar:
    # 1) Remover estados de widgets (evita StreamlitAPIException)
    for itm in st.session_state["items"]:
        for k in (itm["key_done"], itm["key_obs"], itm["key_resp"], itm["key_date"]):
            st.session_state.pop(k, None)

    # 2) Resetar dados internos
    st.session_state["items"] = build_items()

    # 3) Recarregar a página para refletir estado limpo
    st.rerun()

if gerar:
    if not REPORTLAB_OK:
        st.error("Biblioteca **reportlab** não encontrada. Instale com `pip install reportlab` e tente novamente.")
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

st.markdown("---")
st.caption("Dica: conclua as tarefas e registre responsável e data; as concluídas ficam em verde para facilitar a revisão.")
