import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURAÇÃO E DESIGN SYSTEM ARCO ---
st.set_page_config(
    page_title="PEI 360 | Arco Educação",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed" # Menu recolhido para parecer mais App
)

# CSS AVANÇADO (Visual de App Moderno)
st.markdown("""
    <style>
    /* VARIÁVEIS DE COR ARCO */
    :root {
        --arco-blue: #004e92;
        --arco-green: #28a745;
        --bg-app: #f0f2f6;
        --card-bg: #ffffff;
    }
    
    .main {background-color: var(--bg-app);}
    
    /* ESTILO DE CARDS (Para tirar cara de formulário) */
    .app-card {
        background-color: var(--card-bg);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border-left: 5px solid var(--arco-blue);
    }
    
    /* TÍTULOS */
    h1 {color: var(--arco-blue); font-weight: 800; letter-spacing: -1px;}
    h2, h3 {color: #2c3e50; font-family: 'Helvetica Neue', sans-serif;}
    
    /* SLIDERS (Correção da cor vermelha para Azul) */
    div.stSlider > div > div > div > div {
        background-color: var(--arco-blue) !important;
    }
    div.stSlider > div > div > div > div > div {
        color: var(--arco-blue) !important;
    }
    
    /* BOTÕES */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        border-radius: 12px;
        height: 50px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003366;
        transform: translateY(-2px);
    }
    
    /* INPUTS MAIS BONITOS */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ced4da;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE GERAÇÃO DO WORD ---
def gerar_docx_final(dados):
    doc = Document()
    
    # Cabeçalho Limpo
    titulo = doc.add_heading('PEI 360 - PLANO DE ENSINO INDIVIDUALIZADO', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Unidade Escolar: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # Conteúdo Estruturado
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']} | Turma: {dados['turma']}")
    doc.add_paragraph(f"Nascimento: {str(dados['nasc']) if dados['nasc'] else '--'}")
    
    doc.add_heading('2. ESTUDO DE CASO', level=1)
    
    # Indicadores em Destaque
    p_metrics = doc.add_paragraph()
    p_metrics.add_run(f"Nível de Suporte: {dados['nivel_suporte']}").bold = True
    doc.add_paragraph(f"Engajamento: {dados['nivel_engajamento']} | Autonomia: {dados['nivel_autonomia']}")

    if dados['hiperfoco']:
        doc.add_paragraph(f"Hiperfoco (Interesse Potencializador): {dados['hiperfoco']}")
    
    doc.add_heading('Potencialidades:', level=2)
    if dados['potencias']:
        for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
        
    doc.add_heading('Barreiras Mapeadas:', level=2)
    if dados['b_sensorial']: 
        doc.add_paragraph("Sensoriais/Físicas:").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']: 
        doc.add_paragraph("Cognitivas/Aprendizagem:").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']: 
        doc.add_paragraph("Sociais/Comportamentais:").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    doc.add_heading('3. ESTRATÉGIAS PEDAGÓGICAS', level=1)
    doc.add_heading('Adaptações de Acesso:', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
        
    doc.add_heading('Adaptações Curriculares:', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    doc.add_paragraph('\n\n___________________________________\nGestão Pedagógica')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. SESSION STATE ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'cid': '', 'equipe_externa': [], 'historico': '', 'familia': '', 'hiperfoco': '',
        'nivel_suporte': 'Nível 1: Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Em desenvolvimento',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# --- 4. INTERFACE PRINCIPAL (DASHBOARD LAYOUT) ---

# Cabeçalho Moderno (Sem Sidebar na Home para dar amplitude)
c_logo, c_title = st.columns([1, 6])
with c_logo:
    st.markdown("# 🧩")
with c_title:
    st.title("PEI 360")
    st.markdown("### Solução Integrada de Inclusão Escolar")

# Barra de Progresso Visual
progresso = 0
if st.session_state.dados['nome']: progresso += 25
if st.session_state.dados['b_sensorial'] or st.session_state.dados['b_cognitiva']: progresso += 25
if st.session_state.dados['estrategias_acesso']: progresso += 25
if progresso == 75: progresso = 100
st.progress(progresso)

# Navegação por Abas (Visual Limpo)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Visão Geral", 
    "👤 Identificação", 
    "🔍 Estudo de Caso", 
    "🎯 Estratégias", 
    "📄 Documento"
])

# === ABA 1: VISÃO GERAL (Pitch de Venda) ===
with tab1:
    st.markdown("""
    <div class="app-card">
        <h3>Bem-vindo ao Novo Padrão de Inclusão Arco</h3>
        <p>O <b>PEI 360</b> transforma a exigência legal em estratégia pedagógica.</p>
        <br>
        <div style="display: flex; justify-content: space-between;">
            <div style="background: #e3f2fd; padding: 15px; border-radius: 10px; width: 48%;">
                <b>📘 O que é o PEI?</b><br>
                É o planejamento que remove barreiras. Não foca no laudo médico, mas na <b>potencialidade do aluno</b> e na adaptação do ambiente escolar.
            </div>
            <div style="background: #fff3e0; padding: 15px; border-radius: 10px; width: 48%;">
                <b>⚖️ Compliance Legal (2025)</b><br>
                Atende integralmente o <b>Decreto nº 12.773/25</b> (Art. 12), garantindo o PEI independente de laudo clínico.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# === ABA 2: IDENTIFICAÇÃO (Card Visual) ===
with tab2:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("Dados do Estudante")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.dados['nome'] = st.text_input("Nome Completo", value=st.session_state.dados['nome'])
        st.session_state.dados['nasc'] = st.date_input("Data de Nascimento")
        # Campo Genérico para todas as marcas Arco
        st.session_state.dados['escola'] = st.text_input("Unidade Escolar", placeholder="Ex: Escola Santa Maria, Colégio X...", value=st.session_state.dados['escola'])
    with c2:
        st.session_state.dados['serie'] = st.selectbox("Série/Ano", ["Ed. Infantil", "Fund I", "Fund II", "Ensino Médio"])
        st.session_state.dados['turma'] = st.text_input("Turma")
        st.session_state.dados['cid'] = st.text_input("Diagnóstico/Hipótese (Opcional)")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("Contexto Familiar e Histórico")
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("**Histórico Escolar Prévio**")
        st.session_state.dados['historico'] = st.text_area("Ex: Veio de outra escola? Repetiu ano?", height=80)
    with col_h2:
        st.markdown("**Escuta da Família**")
        st.session_state.dados['familia'] = st.text_area("O que a família relata? O que funciona em casa?", height=80)
    st.markdown('</div>', unsafe_allow_html=True)

# === ABA 3: ESTUDO DE CASO (Mapeamento) ===
with tab3:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    col_pot, col_bar = st.columns([1, 1])

    with col_pot:
        st.subheader("🌟 Potencialidades")
        st.info("O que engaja este aluno?")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Interesse Restrito", placeholder="Ex: Dinossauros, Mapas, Games...")
        st.session_state.dados['potencias'] = st.multiselect("Habilidades Fortes:", 
            ["Memória Visual", "Tecnologia", "Artes", "Oralidade", "Lógica", "Música", "Esportes", "Empatia"])
        
        st.markdown("---")
        st.subheader("Indicadores")
        # SLIDERS COM COR CORRIGIDA (AZUL)
        st.session_state.dados['nivel_engajamento'] = st.select_slider(
            "Nível de Engajamento:", options=["Baixo", "Médio", "Alto", "Excelente"], value="Médio"
        )
        st.session_state.dados['nivel_autonomia'] = st.select_slider(
            "Nível de Autonomia:", options=["Requer Apoio Total", "Apoio Parcial", "Autônomo"], value="Apoio Parcial"
        )

    with c_bar:
        st.subheader("🚧 Barreiras (O que atrapalha?)")
        
        with st.expander("Sensorial e Físico", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", 
                ["Hipersensibilidade Auditiva", "Agitação Motora", "Baixa Visão", "Dificuldade Motora"])
        with st.expander("Cognitivo e Acadêmico"):
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", 
                ["Atenção Curta", "Não copia da lousa", "Dificuldade de Leitura", "Rigidez Mental"])
        with st.expander("Social e Comunicacional"):
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", 
                ["Isolamento", "Comportamento Opositor", "Pouca Fala", "Literalidade (não entende ironia)"])
            
        st.markdown("---")
        st.markdown("**Nível de Suporte Geral**")
        st.session_state.dados['nivel_suporte'] = st.select_slider(
            "", options=["Nível 1 (Leve)", "Nível 2 (Moderado)", "Nível 3 (Elevado)"], value="Nível 1 (Leve)"
        )
    st.markdown('</div>', unsafe_allow_html=True)

# === ABA 4: ESTRATÉGIAS (Inteligência) ===
with tab4:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("🎯 Plano de Intervenção")
    
    # Lógica de Sugestão
    sugestoes = []
    if "Hipersensibilidade Auditiva" in st.session_state.dados['b_sensorial']: sugestoes.append("Uso de abafadores de ruído")
    if "Não copia da lousa" in st.session_state.dados['b_cognitiva']: sugestoes.append("Fornecer foto da lousa/material impresso")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso**")
        st.caption("Mudanças em COMO o aluno acessa a aula.")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Estratégias:", 
            options=sugestoes + ["Tempo Estendido", "Auxílio de Leitura (Ledor) e Escrita (Escriba)", "Material Ampliado", "Sentar na frente", "Tablet"],
            default=sugestoes
        )
    with c2:
        st.markdown("**Adaptações Curriculares**")
        st.caption("Mudanças no QUE o aluno aprende/avalia.")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", 
            ["Redução de questões", "Avaliação Oral", "Foco no essencial", "Atividade prática", "Prova Adaptada"])
    st.markdown('</div>', unsafe_allow_html=True)

# === ABA 5: DOCUMENTO ===
with tab5:
    st.markdown('<div class="app-card">', unsafe_allow_html=True)
    st.subheader("🖨️ Documento Oficial")
    
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Preencha o nome do aluno na aba 'Identificação'.")
    else:
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            st.write("")
            st.write("")
            doc_buffer = gerar_docx_final(st.session_state.dados)
            st.download_button(
                label="📥 BAIXAR PEI COMPLETO (.docx)",
                data=doc_buffer,
                file_name=f"PEI_{st.session_state.dados['nome'].strip()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        with col_info:
            st.success(f"**Pronto!** O PEI de {st.session_state.dados['nome']} foi gerado seguindo as diretrizes do Grupo Arco e legislação vigente.")
    st.markdown('</div>', unsafe_allow_html=True)