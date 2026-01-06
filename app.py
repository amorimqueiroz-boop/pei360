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

    /* --- INPUTS VISÍVEIS (CORREÇÃO SOLICITADA) --- */
    /* Deixa claro onde escrever com bordas e fundo branco */
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

    /* --- CARDS PERSONALIZADOS DO TOPO (CORREÇÃO SOLICITADA) --- */
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

    /* --- CARDS DA HOME (O QUE É PEI) --- */
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
    if dados['b_sensorial']: 
        doc.add_paragraph("Sensoriais/Físicas:", style='Heading 3')
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']: 
        doc.add_paragraph("Cognitivas/Aprendizagem:", style='Heading 3')
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']: 
        doc.add_paragraph("Sociais/Comunicação:", style='Heading 3')
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Plano
    doc.add_heading('3. PLANO DE AÇÃO (ESTRATÉGIAS)', level=1)
    
    doc.add_heading('Adaptações de Acesso:', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Nenhuma adaptação necessária.")

    doc.add_heading('Adaptações Curriculares:', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Currículo padrão.")

    doc.add_paragraph('\n\n___________________________\nCoordenação Pedagógica')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. GESTÃO DE ESTADO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'cid': '', 'equipe_externa': [], 'historico': '', 'familia': '', 'hiperfoco': '',
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# --- 4. INTERFACE DO APP ---

# Header Customizado (HTML)
st.markdown("""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
    <div>
        <h1 style='margin:0; font-size: 2.2em;'>PEI 360º</h1>
        <span style='color:grey; font-size:1.1em;'>Plano de Educação Inclusiva | Arco Educação</span>
    </div>
    <div style="text-align:right;">
        <span style='font-size:0.9em; background:#e3f2fd; color:#004e92; padding:5px 10px; border-radius:15px;'>
        Decreto 12.773/25
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# TOP CARDS (Métricas Bonitas)
count_barreiras = len(st.session_state.dados['b_sensorial']) + len(st.session_state.dados['b_cognitiva']) + len(st.session_state.dados['b_social'])
count_estrat = len(st.session_state.dados['estrategias_acesso']) + len(st.session_state.dados['estrategias_curriculo'])
status_doc = "Em Elaboração" if not st.session_state.dados['nome'] else "Pronto"

col_k1, col_k2, col_k3 = st.columns(3)
col_k1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Barreiras Mapeadas</div><div class="kpi-value">{count_barreiras}</div></div>""", unsafe_allow_html=True)
col_k2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Estratégias Definidas</div><div class="kpi-value">{count_estrat}</div></div>""", unsafe_allow_html=True)
col_k3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Status do PEI</div><div class="kpi-value" style="font-size:22px; line-height:34px;">{status_doc}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Abas de Navegação
tab_home, tab_aluno, tab_mapa, tab_acao, tab_final = st.tabs([
    "🏠 Visão Geral", "👤 Identificação", "🔍 Mapeamento", "🛠️ Estratégias", "🖨️ Exportar"
])

# === ABA 1: HOME (CONTEÚDO MELHORADO) ===
with tab_home:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h3>📘 O que é o PEI?</h3>
            <p>O <b>Plano de Ensino Individualizado</b> é o "GPS" da inclusão escolar. Ele traça a rota entre onde o aluno está e onde ele pode chegar.</p>
            <p>Não é um documento burocrático para "arquivar", mas uma ferramenta viva para <b>garantir aprendizado</b>.</p>
            <ul>
                <li>Foco nas potências (o que o aluno já sabe).</li>
                <li>Adaptação do meio (não do aluno).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h3>⚖️ Legislação & Amparo</h3>
            <p>Este sistema garante que sua escola cumpra o <b>Decreto 12.773 (Dez/2025)</b>:</p>
            <div style="background:white; padding:15px; border-left:4px solid #004e92; margin-top:10px; font-style:italic;">
            "Art. 12. As instituições devem elaborar plano individualizado... independentemente de laudo médico."
            </div>
            <p style="margin-top:10px;"><b>Segurança Jurídica:</b> O PEI documenta todas as ações da escola, protegendo a instituição e a família.</p>
        </div>
        """, unsafe_allow_html=True)

# === ABA 2: IDENTIFICAÇÃO (CAMPOS VISÍVEIS) ===
with tab_aluno:
    st.markdown("### 1. Dados do Estudante")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'], placeholder="Digite o nome do aluno...")
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento")
    
    c3, c4 = st.columns(2)
    st.session_state.dados['escola'] = c3.text_input("Escola", st.session_state.dados['escola'], placeholder="Nome da Escola ou Unidade...")
    st.session_state.dados['serie'] = c4.selectbox("Série/Ano", ["Educação Infantil", "Fund I (1º ao 5º)", "Fund II (6º ao 9º)", "Ensino Médio"])
    st.session_state.dados['turma'] = c3.text_input("Turma", placeholder="Ex: 3º B")
    st.session_state.dados['cid'] = c4.text_input("CID/Diagnóstico (Opcional)", placeholder="Se houver laudo...")

    st.markdown("---")
    st.markdown("### 2. Contexto (Histórico e Família)")
    
    col_h, col_f = st.columns(2)
    with col_h:
        st.markdown("**Histórico Escolar**")
        st.caption("Repetências, transferências ou observações anteriores.")
        st.session_state.dados['historico'] = st.text_area("Histórico", height=120, label_visibility="collapsed", placeholder="Digite aqui o histórico escolar prévio...")
    
    with col_f:
        st.markdown("**Relato da Família**")
        st.caption("O que a família relata sobre o comportamento em casa?")
        st.session_state.dados['familia'] = st.text_area("Família", height=120, label_visibility="collapsed", placeholder="Digite aqui as observações da família...")

    st.markdown("---")
    st.session_state.dados['equipe_externa'] = st.multiselect("Rede de Apoio Externa", 
        ["Psicólogo", "Fonoaudiólogo", "T.O.", "Neuropediatra", "Psicopedagogo"],
        placeholder="Selecione os profissionais..."
    )

# === ABA 3: MAPEAMENTO ===
with tab_mapa:
    c_pot, c_bar = st.columns(2)
    
    with c_pot:
        st.markdown("### 🌟 Potências")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco (Interesse Intenso)", placeholder="Ex: Dinossauros, Mapas, Games...")
        st.session_state.dados['potencias'] = st.multiselect("Habilidades Fortes", 
            ["Memória Visual", "Tecnologia", "Desenho", "Oralidade", "Lógica", "Música"],
            placeholder="Selecione as habilidades..."
        )
        
        st.markdown("<br>**Engajamento Escolar**", unsafe_allow_html=True)
        engaj = st.select_slider("", options=["Baixo", "Médio", "Alto"], value="Médio", key="eng")
        st.markdown(f"<div class='status-info'>{engaj}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_engajamento'] = engaj
        
        st.markdown("**Autonomia (AVDs)**")
        auto = st.select_slider("", options=["Dependente", "Supervisão Parcial", "Autônomo"], value="Supervisão Parcial", key="aut")
        st.markdown(f"<div class='status-ok'>{auto}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_autonomia'] = auto

    with c_bar:
        st.markdown("### 🚧 Barreiras")
        
        with st.expander("Sensorial e Físico", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", 
                ["Hipers