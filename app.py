import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="PEI 360º | Arco",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS REFINADO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    :root {
        --arco-blue: #004e92;
        --arco-orange: #ff7f00;
        --input-border: #CBD5E0;
        --input-bg: #FFFFFF;
    }

    /* Inputs Visíveis */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important;
        background-color: var(--input-bg) !important;
        border-radius: 6px !important;
        padding: 10px !important;
        color: #2D3748 !important;
    }
    
    /* Cards do Topo */
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

    /* Cards da Home */
    .home-card {
        background: #F7FAFC;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        height: 100%;
    }
    
    /* Botões */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        height: 3em;
        width: 100%;
    }
    .stButton>button:hover { background-color: #003a6e; }

    /* Status Text */
    .status-ok { color: #28a745; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    .status-info { color: #004e92; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LÓGICA WORD ---
def gerar_docx_final(dados):
    doc = Document()
    
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

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

    doc.add_heading('2. MAPEAMENTO PEDAGÓGICO', level=1)
    doc.add_paragraph(f"Nível de Suporte: {dados['nivel_suporte']}")
    doc.add_paragraph(f"Engajamento: {dados['nivel_engajamento']} | Autonomia: {dados['nivel_autonomia']}")

    doc.add_heading('Potencialidades e Hiperfoco:', level=2)
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')

    doc.add_heading('Barreiras Identificadas:', level=2)
    if dados['b_sensorial']: 
        p = doc.add_paragraph()
        p.add_run("Sensoriais/Físicas:").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']: 
        p = doc.add_paragraph()
        p.add_run("Cognitivas/Aprendizagem:").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']: 
        p = doc.add_paragraph()
        p.add_run("Sociais/Comunicação:").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

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

# --- 3. ESTADO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'cid': '', 'equipe_externa': [], 'historico': '', 'familia': '', 'hiperfoco': '',
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# --- 4. INTERFACE ---
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

# TOP CARDS
count_barreiras = len(st.session_state.dados['b_sensorial']) + len(st.session_state.dados['b_cognitiva']) + len(st.session_state.dados['b_social'])
count_estrat = len(st.session_state.dados['estrategias_acesso']) + len(st.session_state.dados['estrategias_curriculo'])
status_doc = "Em Elaboração" if not st.session_state.dados['nome'] else "Pronto"

c1, c2, c3 = st.columns(3)
c1.markdown(f"""<div class="kpi-card"><div class="kpi-title">Barreiras</div><div class="kpi-value">{count_barreiras}</div></div>""", unsafe_allow_html=True)
c2.markdown(f"""<div class="kpi-card"><div class="kpi-title">Estratégias</div><div class="kpi-value">{count_estrat}</div></div>""", unsafe_allow_html=True)
c3.markdown(f"""<div class="kpi-card"><div class="kpi-title">Status</div><div class="kpi-value" style="font-size:22px; line-height:34px;">{status_doc}</div></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Visão Geral", "👤 Identificação", "🔍 Mapeamento", "🛠️ Estratégias", "🖨️ Exportar"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h3>📘 O que é o PEI?</h3>
            <p>O <b>Plano de Ensino Individualizado</b> é o "GPS" da inclusão escolar. Ele traça a rota entre onde o aluno está e onde ele pode chegar.</p>
            <p>Não é um documento burocrático, mas uma ferramenta viva para <b>garantir aprendizado</b>.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h3>⚖️ Legislação & Amparo</h3>
            <p>Este sistema garante que sua escola cumpra o <b>Decreto 12.773 (Dez/2025)</b>.</p>
            <div style="background:white; padding:15px; border-left:4px solid #004e92; margin-top:10px; font-style:italic;">
            "Art. 12. As instituições devem elaborar plano individualizado... independentemente de laudo médico."
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 1. Dados do Estudante")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'], placeholder="Digite o nome...")
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento")
    
    c3, c4 = st.columns(2)
    st.session_state.dados['escola'] = c3.text_input("Escola", st.session_state.dados['escola'])
    st.session_state.dados['serie'] = c4.selectbox("Série", ["Ed. Infantil", "Fund I", "Fund II", "Médio"])
    st.session_state.dados['turma'] = c3.text_input("Turma")
    st.session_state.dados['cid'] = c4.text_input("CID (Opcional)")

    st.markdown("---")
    c_h, c_f = st.columns(2)
    with c_h:
        st.markdown("**Histórico Escolar**")
        st.session_state.dados['historico'] = st.text_area("Histórico", height=100, label_visibility="collapsed", placeholder="Histórico prévio...")
    with c_f:
        st.markdown("**Relato da Família**")
        st.session_state.dados['familia'] = st.text_area("Família", height=100, label_visibility="collapsed", placeholder="Relato familiar...")
    
    st.markdown("---")
    eq_opcoes = ["Psicólogo", "Fonoaudiólogo", "T.O.", "Neuropediatra", "Psicopedagogo"]
    st.session_state.dados['equipe_externa'] = st.multiselect("Rede de Apoio Externa", eq_opcoes)

with tab3:
    c_pot, c_bar = st.columns(2)
    with c_pot:
        st.markdown("### 🌟 Potências")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco", placeholder="Ex: Dinossauros...")
        pot_opcoes = ["Memória Visual", "Tecnologia", "Desenho", "Oralidade", "Lógica", "Música"]
        st.session_state.dados['potencias'] = st.multiselect("Habilidades", pot_opcoes)
        
        st.markdown("<br>**Engajamento**", unsafe_allow_html=True)
        eng = st.select_slider("", ["Baixo", "Médio", "Alto"], value="Médio", key="eng")
        st.markdown(f"<div class='status-info'>{eng}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_engajamento'] = eng
        
        st.markdown("**Autonomia**")
        aut = st.select_slider("", ["Dependente", "Supervisão Parcial", "Autônomo"], value="Supervisão Parcial", key="aut")
        st.markdown(f"<div class='status-ok'>{aut}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_autonomia'] = aut

    with c_bar:
        st.markdown("### 🚧 Barreiras")
        with st.expander("Sensorial e Físico", expanded=True):
            op_sen = ["Hipersensibilidade Auditiva", "Agitação Motora", "Baixa Visão", "Coordenação Motora"]
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", op_sen)
        with st.expander("Cognitivo"):
            op_cog = ["Atenção Curta", "Não copia do quadro", "Dificuldade Leitura", "Rigidez Cognitiva"]
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", op_cog)
        with st.expander("Social"):
            op_soc = ["Isolamento", "Opositor", "Pouca comunicação verbal", "Ecolalia"]
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", op_soc)
        
        st.markdown("<br>**Suporte Necessário**", unsafe_allow_html=True)
        sup = st.select_slider("", ["Leve", "Moderado", "Elevado (AT)"], value="Leve", key="sup")
        st.markdown(f"<div class='status-info'>{sup}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_suporte'] = sup

with tab4:
    st.markdown("### 🚀 Plano de Ação")
    sug = []
    if "Hipersensibilidade Auditiva" in st.session_state.dados['b_sensorial']: sug.append("Uso de abafadores")
    if "Não copia do quadro" in st.session_state.dados['b_cognitiva']: sug.append("Fornecer pauta impressa/foto")
    
    c1, c2 = st.columns(2)
    with c1:
        st.info("Adaptações de Acesso")
        op_acc = ["Tempo estendido", "Ledor e Escriba", "Material ampliado", "Uso de Tablet", "Sentar à frente"]
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Estratégias:", options=sug+op_acc, default=sug)
    with c2:
        st.info("Adaptações Curriculares")
        op_cur = ["Redução de questões", "Priorização de conteúdo", "Avaliação Oral", "Prova Adaptada", "Atividade Prática"]
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", op_cur)

with tab5:
    st.markdown("<div style='text-align:center; padding: 20px;'>", unsafe_allow_html=True)
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Preencha o nome do aluno na aba 'Identificação'.")
    else:
        st.success("✅ Documento compilado!")
        doc_file = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 BAIXAR PEI EM WORD (.DOCX)", doc_file, f"PEI_{st.session_state.dados['nome'].strip()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown("</div>", unsafe_allow_html=True)
