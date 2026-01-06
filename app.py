import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURAÇÃO E DESIGN SYSTEM (VISUAL DASHBOARD) ---
st.set_page_config(
    page_title="PEI 360º | Inclusão",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar recolhida para dar ar de 'App'
)

# CSS AVANÇADO PARA "CARA DE SOFTWARE"
st.markdown("""
    <style>
    /* Importando fonte limpa */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Cores Arco Educação */
    :root {
        --arco-blue: #004e92;
        --arco-green: #28a745;
        --bg-color: #f0f2f6;
        --card-bg: #ffffff;
    }

    /* Fundo geral */
    .stApp {
        background-color: var(--bg-color);
    }

    /* Estilo dos CARTÕES (Cards) - O segredo do design */
    .css-card {
        background-color: var(--card-bg);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    
    /* Títulos */
    h1 {color: var(--arco-blue); font-weight: 700; letter-spacing: -1px;}
    h2, h3 {color: #2c3e50; font-weight: 600;}
    
    /* Métricas no topo */
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-top: 4px solid var(--arco-blue);
    }

    /* Botões */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        border: none;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #003d73;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* Feedback dos Sliders (Corrigindo o vermelho) */
    .feedback-azul {
        color: var(--arco-blue);
        font-weight: bold;
        font-size: 0.9rem;
        margin-top: -15px;
        margin-bottom: 10px;
    }
    .feedback-verde {
        color: var(--arco-green);
        font-weight: bold;
        font-size: 0.9rem;
        margin-top: -15px;
        margin-bottom: 10px;
    }
    
    /* Ajuste de Espaçamento */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE WORD (LÓGICA) ---
def gerar_docx_final(dados):
    doc = Document()
    
    # Cabeçalho
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Instituição: {dados["escola"]} | Ano Letivo: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Identificação
    doc.add_heading('1. CONTEXTO DO ESTUDANTE', level=1)
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False 
    celulas = tbl.rows[0].cells
    celulas[0].text = f"Nome: {dados['nome']}\nNascimento: {str(dados['nasc']) if dados['nasc'] else '--'}"
    celulas[1].text = f"Série: {dados['serie']}\nTurma: {dados['turma']}"
    
    doc.add_paragraph(f"\nDiagnóstico/Hipótese: {dados['cid']}")
    doc.add_paragraph(f"Equipe Multidisciplinar: {', '.join(dados['equipe_externa']) if dados['equipe_externa'] else 'Não possui.'}")
    
    if dados['historico']:
        doc.add_heading('Histórico Escolar:', level=2)
        doc.add_paragraph(dados['historico'])
    
    if dados['familia']:
        doc.add_heading('Escuta da Família:', level=2)
        doc.add_paragraph(dados['familia'])

    # 2. Perfil
    doc.add_heading('2. MAPA DE DESENVOLVIMENTO', level=1)
    
    p = doc.add_paragraph()
    p.add_run(f"Nível de Suporte: {dados['nivel_suporte']}").bold = True
    doc.add_paragraph(f"Engajamento Escolar: {dados['nivel_engajamento']}")
    doc.add_paragraph(f"Autonomia (AVDs): {dados['nivel_autonomia']}")

    doc.add_heading('Hiperfoco e Potencialidades:', level=2)
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')

    doc.add_heading('Mapeamento de Barreiras:', level=2)
    if dados['b_sensorial']: 
        doc.add_paragraph("Sensoriais/Físicas:", style='Heading 3')
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']: 
        doc.add_paragraph("Cognitivas/Aprendizagem:", style='Heading 3')
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']: 
        doc.add_paragraph("Sociais/Comunicação:", style='Heading 3')
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Estratégias
    doc.add_heading('3. ESTRATÉGIAS PEDAGÓGICAS', level=1)
    
    doc.add_heading('Adaptações de Acesso:', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Nenhuma adaptação de acesso necessária.")

    doc.add_heading('Adaptações Curriculares:', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Segue currículo padrão.")

    doc.add_paragraph('\n\n___________________________\nCoordenação Pedagógica')
    doc.add_paragraph('\n___________________________\nResponsável Legal')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. ESTADO (MEMÓRIA) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'cid': '', 'equipe_externa': [], 'historico': '', 'familia': '', 'hiperfoco': '',
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# --- 4. INTERFACE DASHBOARD ---

# Topo: Logo e Título
col_head1, col_head2 = st.columns([1, 6])
with col_head1:
    st.markdown("<h1>🧩</h1>", unsafe_allow_html=True)
with col_head2:
    st.markdown("<h1>PEI 360º <span style='font-size:20px; color:#666; font-weight:400'>| Plano de Educação Inclusiva</span></h1>", unsafe_allow_html=True)

# Métricas em Tempo Real (Painel Vivo)
tot_barreiras = len(st.session_state.dados['b_sensorial']) + len(st.session_state.dados['b_cognitiva']) + len(st.session_state.dados['b_social'])
tot_estrategias = len(st.session_state.dados['estrategias_acesso']) + len(st.session_state.dados['estrategias_curriculo'])

m1, m2, m3 = st.columns(3)
m1.metric("Barreiras Mapeadas", tot_barreiras, delta_color="inverse")
m2.metric("Estratégias Definidas", tot_estrategias)
m3.metric("Status do PEI", "Em Elaboração" if not st.session_state.dados['nome'] else "Pronto para Gerar", delta="Online")

st.markdown("---")

# Abas "Clean"
tab_educ, tab_aluno, tab_mapa, tab_acao, tab_final = st.tabs([
    "📘 Visão Geral & Lei", "👤 Identificação", "🔍 Estudo de Caso", "🚀 Estratégias", "🖨️ Emitir PEI"
])

# === ABA 1: EDUCAÇÃO ===
with tab_educ:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="css-card">
        <h3>O que é o PEI 360º?</h3>
        <p>Uma ferramenta de gestão pedagógica que traduz a legislação em prática escolar.</p>
        <p><b>Diferenciais:</b></p>
        <ul>
        <li>Foco na potencialidade (Hiperfoco).</li>
        <li>Eliminação de barreiras (Não foco na doença).</li>
        <li>Documentação jurídica automática.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="css-card">
        <h3>Compliance 2025</h3>
        <p style='font-size: 0.9em; color: #666;'>Baseado no Decreto 12.773/25 e LBI.</p>
        <div style='background:#e8f4f8; padding:10px; border-radius:5px; border-left: 4px solid #004e92;'>
        "A escola deve prover adaptações razoáveis e plano individualizado, independentemente de laudo médico."
        </div>
        </div>
        """, unsafe_allow_html=True)

# === ABA 2: IDENTIFICAÇÃO ===
with tab_aluno:
    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### Dados do Estudante")
        c1, c2 = st.columns(2)
        st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
        st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento")
        
        c3, c4 = st.columns(2)
        st.session_state.dados['escola'] = c3.text_input("Unidade Escolar / Marca", st.session_state.dados['escola'], placeholder="Ex: Colégio X / Plataforma Y")
        st.session_state.dados['serie'] = c4.selectbox("Série/Ano", ["Ed. Infantil", "Fund I", "Fund II", "Ensino Médio"])
        st.session_state.dados['turma'] = c3.text_input("Turma")
        st.session_state.dados['cid'] = c4.text_input("CID/Diagnóstico (Opcional)")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### Contexto Familiar e Histórico")
        st.session_state.dados['historico'] = st.text_area("Histórico Escolar (Escolas anteriores, repetências):", height=100)
        st.session_state.dados['familia'] = st.text_area("Relato da Família (O que funciona em casa?):", height=100)
        st.session_state.dados['equipe_externa'] = st.multiselect("Rede de Apoio:", ["Psicólogo", "Fonoaudiólogo", "T.O.", "Neuropediatra", "Psicopedagogo"])
        st.markdown('</div>', unsafe_allow_html=True)

# === ABA 3: MAPEAMENTO ===
with tab_mapa:
    c_pot, c_bar = st.columns(2)
    
    with c_pot:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### 🌟 Potências e Hiperfoco")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco (Interesse intenso):", placeholder="Ex: Dinossauros, Tecnologia...")
        st.session_state.dados['potencias'] = st.multiselect("Habilidades:", 
            ["Memória Visual", "Tecnologia", "Desenho", "Oralidade", "Lógica", "Música", "Afetividade"])
        
        st.markdown("---")
        st.markdown("**Nível de Engajamento**")
        engaj = st.select_slider("", options=["Baixo", "Médio", "Alto"], value="Médio", key="sl_eng")
        st.markdown(f"<div class='feedback-azul'>Status: {engaj}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_engajamento'] = engaj
        
        st.markdown("**Nível de Autonomia**")
        auto = st.select_slider("", options=["Dependente", "Supervisão Parcial", "Autônomo"], value="Supervisão Parcial", key="sl_auto")
        st.markdown(f"<div class='feedback-verde'>Status: {auto}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_autonomia'] = auto
        st.markdown('</div>', unsafe_allow_html=True)

    with c_bar:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.markdown("### 🚧 Mapeamento de Barreiras")
        st.caption("Selecione apenas o que se aplica:")
        
        with st.expander("Sensorial e Físico"):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", 
                ["Hipersensibilidade Auditiva", "Agitação Motora", "Baixa Visão", "Dificuldade Motora Fina"])
        with st.expander("Cognitivo e Atenção"):
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", 
                ["Atenção Curta", "Não copia do quadro", "Dificuldade de Leitura", "Rigidez Cognitiva"])
        with st.expander("Social e Comunicação"):
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", 
                ["Isolamento", "Comportamento Opositor", "Pouca comunicação verbal", "Ecolalia"])
        
        st.markdown("---")
        st.markdown("**Nível de Suporte Geral**")
        sup = st.select_slider("", options=["Leve", "Moderado", "Elevado (AT)"], value="Leve", key="sl_sup")
        st.markdown(f"<div class='feedback-azul'>Necessidade: {sup}</div>", unsafe_allow_html=True)
        st.session_state.dados['nivel_suporte'] = sup
        st.markdown('</div>', unsafe_allow_html=True)

# === ABA 4: ESTRATÉGIAS ===
with tab_acao:
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Plano de Ação")
    st.info("Estratégias sugeridas com base no mapeamento anterior.")
    
    # Lógica de Sugestão
    sug_acesso = []
    if "Hipersensibilidade Auditiva" in st.session_state.dados['b_sensorial']: sug_acesso.append("Uso de abafadores")
    if "Não copia do quadro" in st.session_state.dados['b_cognitiva']: sug_acesso.append("Fornecer pauta impressa/foto")
    if "Dificuldade de Leitura" in st.session_state.dados['b_cognitiva']: sug_acesso.append("Ledor e Escriba")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Adaptações de Acesso")
        st.caption("Como o aluno acessa?")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Selecione:", 
            options=sug_acesso + ["Tempo estendido", "Ledor e Escriba", "Material ampliado", "Uso de Tablet"],
            default=sug_acesso)
    with c2:
        st.markdown("#### Adaptações Curriculares")
        st.caption("O que o aluno aprende?")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Selecione:", 
            ["Redução de questões", "Priorização de conteúdo", "Avaliação Oral", "Prova Adaptada"])
    st.markdown('</div>', unsafe_allow_html=True)

# === ABA 5: FINAL ===
with tab_final:
    col_centro = st.columns([1, 2, 1])
    with col_centro[1]:
        st.markdown('<div class="css-card" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown("### 📄 Tudo Pronto!")
        
        if not st.session_state.dados['nome']:
            st.warning("Preencha o nome do aluno na aba 'Identificação'.")
        else:
            doc_file = gerar_docx_final(st.session_state.dados)
            st.markdown(f"**Aluno:** {st.session_state.dados['nome']}")
            st.markdown(f"**Barreiras:** {tot_barreiras} | **Estratégias:** {tot_estrategias}")
            
            st.download_button(
                label="📥 BAIXAR PEI 360º (.DOCX)",
                data=doc_file,
                file_name=f"PEI_{st.session_state.dados['nome'].strip()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        st.markdown('</div>', unsafe_allow_html=True)