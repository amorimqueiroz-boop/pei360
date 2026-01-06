import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURAÇÃO VISUAL & CSS (ARCO EDUCAÇÃO) ---
st.set_page_config(
    page_title="PEI 360º | Arco",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS REFINADO (VISIBILIDADE E UX)
st.markdown("""
    <style>
    /* Importando Fontes */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    /* Cores Globais */
    :root {
        --arco-blue: #004e92;
        --arco-orange: #ff7f00;
        --input-border: #CBD5E0;
        --input-bg: #FFFFFF;
    }

    /* --- INPUTS VISÍVEIS --- */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important;
        background-color: var(--input-bg) !important;
        border-radius: 6px !important;
        padding: 10px !important;
        color: #2D3748 !important;
    }
    
    /* Foco no input */
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--arco-blue) !important;
        box-shadow: 0 0 0 1px var(--arco-blue) !important;
    }

    /* --- CARDS PERSONALIZADOS --- */
    .kpi-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid var(--arco-orange);
        text-align: center;
    }
    .kpi-title { font-size: 14px; color: #718096; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 28px; color: var(--arco-blue); font-weight: 800; }

    /* --- CARDS DA HOME --- */
    .home-card {
        background: #F7FAFC;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        height: 100%;
    }
    .home-card h3 { color: var(--arco-blue); margin-top: 0; }
    
    /* --- BOTÕES --- */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        height: 3em;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover { background-color: #003a6e; }

    /* Feedback Visual (Sliders) */
    .status-ok { color: #28a745; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    .status-info { color: #004e92; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA DE GERAÇÃO DO DOCUMENTO WORD ---
def gerar_docx_final(dados):
    doc = Document()
    
    # Cabeçalho
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Identificação
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False 
    celulas = tbl.rows[0].cells
    celulas[0].text = f"Nome: {dados['nome']}\nNascimento: {str(dados['nasc']) if dados['nasc'] else '--'}"
    celulas[1].text = f"Série: {dados['serie']}\nTurma: {dados['turma']}"
    
    doc.add_paragraph(f"\nDiagnóstico/Hipótese: {dados['cid']}")
    doc.add_paragraph(f"Equipe Externa: {', '.join(dados['equipe_externa']) if dados['equipe_externa'] else 'Não possui.'}")

    if dados['historico']:
        doc.add_heading('Histórico Escolar:', level=2)
        doc.add_paragraph(dados['historico'])
    if dados['familia']:
        doc.add_heading('Relato da Família:', level=2)
        doc.add_paragraph(dados['familia'])

    # 2. Mapeamento
    doc.add_heading('2. MAPEAMENTO PEDAGÓGICO', level=1)
    doc.add_paragraph(f"Nível de Suporte: {dados['nivel_suporte']}")
    doc.add_paragraph(f"Engajamento: {dados['nivel_engajamento']} | Autonomia: {dados['nivel_autonomia']}")

    doc.add_heading('Potencialidades e Hiperfoco:', level=2)
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')

    doc.add_heading('Barreiras Identificadas:', level=2)
    # Correção do Erro de Style: Usando .bold = True (