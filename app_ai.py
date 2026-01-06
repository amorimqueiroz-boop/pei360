import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PEI 360º | Arco AI", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO VISUAL (IDENTIDADE ARCO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    /* Cores da Identidade */
    :root { --arco-blue: #004e92; --arco-orange: #ff7f00; --input-border: #CBD5E0; --input-bg: #FFFFFF; }
    
    /* Ajustes de Input */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important; 
        background-color: var(--input-bg) !important; 
        border-radius: 8px !important; 
        color: #2D3748 !important; 
    }
    
    /* Botão Principal */
    .stButton>button { 
        background-color: var(--arco-blue); 
        color: white; 
        font-weight: 600; 
        border-radius: 8px; 
        border: none; 
        height: 3em; 
        width: 100%; 
        transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.02); }
    
    /* Cartões */
    .home-card { 
        background: #F8FAFC; 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #E2E8F0; 
        height: 100%; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .home-card h3 { color: var(--arco-blue); margin-top: 0; margin-bottom: 10px;}
    
    /* Dicas de Ajuda */
    .help-text { 
        font-size: 0.9em; 
        color: #4A5568; 
        background-color: #EBF8FF; 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 4px solid #3182CE; 
        margin-bottom: 10px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GEMINI AI (MODELO FLASH) ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ Por favor, insira sua chave de API na barra lateral."
    try:
        genai.configure(api_key=api_key)
        # Atualizado para o modelo Flash (mais rápido e amigável)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Você é um Assistente Pedagógico especialista em Inclusão Escolar.
        Seu tom deve ser acolhedor, técnico e prático.
        
        PERFIL DO ALUNO:
        Nome: {dados['nome']} | Série: {dados['serie']}
        Hiperfoco/Interesse: {dados['hiperfoco']}
        Barreiras Identificadas: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}.
        
        TAREFA:
        Gere sugestões personalizadas para o PEI deste aluno:
        1. Como usar o interesse em "{dados['hiperfoco']}" para motivar o aluno?
        2. Adaptações de Acesso (Ambiente/Material) para as barreiras citadas.
        3. Adaptações Curriculares (Conteúdo/Avaliação) recomendadas.
        
        Responda com empatia e foco na potencialidade do estudante.
        """
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, f"Erro na conexão com o Assistente: {str(e)}"

# --- GERADOR DE DOCUMENTO WORD ---
def gerar_docx_final(dados):
    doc = Document()
    
    # Cabeçalho
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    # 1. Identificação
    doc.add_heading('1. IDENTIFICAÇÃO E CONTEXTO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    tipo_diag = "Diagnóstico Clínico (Laudo)" if dados['tem_laudo'] else "Hipótese Diagnóstica (Em investigação)"
    doc.add_paragraph(f"{tipo_diag}: {dados['diagnostico']}")
    
    if dados['historico']: 
        doc.add_heading('Histórico Escolar:', level=2)
        doc.add_paragraph(dados['historico'])
    if dados['familia']: 
        doc.add_heading('Escuta da Família:', level=2)
        doc.add_paragraph(dados['familia'])

    # 2. Mapeamento
    doc.add_heading('2. MAPEAMENTO PEDAGÓGICO', level=1)
    doc.add_paragraph(f"Suporte: {dados['nivel_suporte']} | Engajamento: {dados['nivel_engajamento']}")
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco/Interesse: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
    
    doc.add_heading('Barreiras Mapeadas:', level=2)
    if dados['b_sensorial']:
        p = doc.add_paragraph(); p.add_run("Sensoriais/Físicas: ").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']:
        p = doc.add_paragraph(); p.add_run("Cognitivas/Aprendizagem: ").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']:
        p = doc.add_paragraph(); p.add_run("Sociais/Comportamentais: ").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Plano de Ação
    doc.add_heading('3. PLANO DE AÇÃO E ESTRATÉGIAS', level=1)
    
    if dados['ia_sugestao']:
        doc.add_heading('Sugestões do Assistente de IA:', level=2)
        doc.add_paragraph(dados['ia_sugestao'])
    
    doc.add_heading('Estratégias Definidas pela Escola:', level=2)
    doc.add_paragraph("Adaptações de Acesso:", style='Heading 3')
    for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    
    doc.add_paragraph("Adaptações Curriculares:", style='Heading 3')
    for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    doc.add_paragraph('\n___________________________\nCoordenação Pedagógica')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'tem_laudo': False, 'diagnostico': '', 'equipe_externa': [], 
        'historico': '', 'familia': '', 'hiperfoco': '', 
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [], 
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    st.markdown("### ⚙️ Configuração")
    api_key = st.text_input("Chave de API (Google AI):", type="password", placeholder="Cole sua chave AIza...")
    if not api_key: st.warning("Cole a chave para ativar o Assistente.")
    st.markdown("---")
    st.info("Sistema v4.1 | Assistente IA Ativo")

# --- CABEÇALHO ---
st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 12px; border-radius:15px; font-weight:600;'>AI EDITION</span>", unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "🤖 Assistente IA", "✅ Plano de Ação", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# ABA 1: INÍCIO
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h3>📘 O que é o PEI?</h3>
            <p>O <b>Plano de Ensino Individualizado (PEI)</b> é o mapa da inclusão. Ele transforma direitos legais em prática pedagógica, garantindo que cada aluno tenha as ferramentas certas para aprender.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h3>🤖 Novo Assistente Inteligente</h3>
            <p>Nesta versão, contamos com um <b>Assistente de IA</b> que ajuda a pensar em adaptações criativas baseadas no hiperfoco do aluno. Use a aba "Assistente IA" para experimentar.</p>
        </div>
        """, unsafe_allow_html=True)

# ABA 2: DADOS
with tab2:
    st.markdown("### 1. Quem é o estudante?")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento")
    st.session_state.dados['escola'] = c1.text_input("Unidade Escolar", st.session_state.dados['escola'])
    st.session_state.dados['serie'] = c2.selectbox("Ano/Série", ["Ed. Infantil", "1º Ano Fund I", "2º Ano Fund I", "3º Ano Fund I", "4º Ano Fund I", "5º Ano Fund I", "6º Ano Fund II", "7º Ano Fund II", "8º Ano Fund II", "9º Ano Fund II", "Ensino Médio"])
    
    st.markdown("---")
    st.markdown("### 2. Contexto Clínico")
    col_laudo, col_diag = st.columns([1, 2])
    with col_laudo:
        st.write("") 
        st.write("") 
        st.session_state.dados['tem_laudo'] = st.checkbox("Possui Laudo Médico?")
    with col_diag:
        label_diag = "Qual o diagnóstico?" if st.session_state.dados['tem_laudo'] else "Qual a hipótese diagnóstica?"
        st.session_state.dados['diagnostico'] = st.text_input(label_diag, st.session_state.dados['diagnostico'])

    st.markdown("---")
    st.markdown("### 3. Histórico e Família")
    c_h, c_f = st.columns(2)
    with c_h:
        st.markdown('<div class="help-text">🏫 <b>Histórico Escolar:</b> Retenções, escolas anteriores, relação com professores.</div>', unsafe_allow_html=True)
        st.session_state.dados['historico'] = st.text_area("Resumo do Histórico", height=120)
    with c_f:
        st.markdown('<div class="help-text">👨‍👩‍👦 <b>Escuta da Família:</b> O que os pais esperam? Como é a rotina em casa?</div>', unsafe_allow_html=True)
        st.session_state.dados['familia'] = st.text_area("Relato da Família", height=120)

# ABA 3: MAPEAMENTO
with tab3:
    st.info("O segredo do PEI é focar no que o aluno JÁ SABE (Potência) para superar o que ele AINDA NÃO SABE (Barreira).")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🚀 Potencialidades & Interesses")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco (O que ele AMA?)", placeholder="Ex: Minecraft, Dinossauros, Música...")
        opcoes_pot = ["Memória Visual", "Facilidade com Tecnologia", "Habilidade Artística", "Boa Oralidade", "Raciocínio Lógico", "Vínculo Afetivo Fácil"]
        st.session_state.dados['potencias'] = st.multiselect("Pontos Fortes", opcoes_pot)
        eng = st.select_slider("Nível de Engajamento Atual", ["Baixo", "Médio", "Alto"], value="Médio"); st.session_state.dados['nivel_engajamento'] = eng
    with c2:
        st.markdown("### 🚧 Barreiras de Aprendizagem")
        with st.expander("Sensorial e Físico", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", ["Hipersensibilidade ao barulho", "Busca Sensorial", "Agitação Motora", "Dificuldade Motora Fina"])
        with st.expander("Cognitivo e Pedagógico"):
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", ["Atenção Flutuante", "Dificuldade de Leitura", "Rigidez de Pensamento", "Dificuldade de Abstração"])
        with st.expander("Social e Emocional"):
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", ["Isolamento", "Baixa tolerância à frustração", "Dificuldade de comunicação", "Ansiedade"])
        sup = st.select_slider("Nível de Suporte Necessário", ["Leve", "Moderado", "Intenso"], value="Leve"); st.session_state.dados['nivel_suporte'] = sup

# ABA 4: ASSISTENTE IA (MODIFICADA)
with tab4:
    c_ia1, c_ia2 = st.columns([1, 2])
    with c_ia1:
        st.markdown("### 🤖 Assistente de IA")
        st.markdown("""
        <div style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; font-size: 0.9rem;">
        Olá! Sou seu assistente virtual.
        <br><br>
        Vou analisar o <b>Hiperfoco</b> e as <b>Barreiras</b> que você mapeou para sugerir estratégias pedagógicas personalizadas.
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("✨ Pedir sugestões ao Assistente"):
            if not st.session_state.dados['nome']:
                st.warning("Preencha pelo menos o nome do aluno na aba 'Aluno'.")
            else:
                with st.spinner("O Assistente está pensando..."):
                    res, err = consultar_ia(api_key, st.session_state.dados)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Sugestões geradas com sucesso!")
    with c_ia2:
        st.markdown("### 💡 Sugestões Geradas")
        st.session_state.dados['ia_sugestao'] = st.text_area("Edite as sugestões antes de salvar:", st.session_state.dados['ia_sugestao'], height=450)

# ABA 5: PLANO DE AÇÃO
with tab5:
    st.markdown("### ✅ Plano de Ação Educacional")
    c_acao1, c_acao2 = st.columns(2)
    with c_acao1:
        st.markdown("#### Adaptações de Acesso (Meio)")
        st.caption("Mudanças no ambiente, material ou forma de dar a aula.")
        opcoes_acesso = ["Tempo estendido para atividades", "Ledor e Escriba", "Material ampliado (Fonte 24+)", "Uso de Tablet/Tecnologia", "Sentar longe de janelas/portas", "Uso de fones abafadores", "Pausas ativas programadas"]
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Selecione as adaptações:", options=opcoes_acesso)
    with c_acao2:
        st.markdown("#### Adaptações Curriculares (Fim)")
        st.caption("Mudanças no conteúdo, objetivos ou avaliação.")
        opcoes_curriculo = ["Redução do número de questões", "Priorização de conteúdo essencial", "Avaliação Oral", "Prova com consulta", "Atividades práticas/concretas", "Fragmentação de tarefas complexas"]
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Selecione as adaptações:", options=opcoes_curriculo)

# ABA 6: DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if not st.session_state.dados['nome']:
        st.warning("⚠️ O documento precisa que o nome do aluno esteja preenchido.")
    else:
        st.success("✅ Seu PEI está pronto para ser gerado!")
        doc_file = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 BAIXAR PEI COMPLETO (.DOCX)", doc_file, f"PEI_{st.session_state.dados['nome'].strip()}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    st.markdown("</div>", unsafe_allow_html=True)