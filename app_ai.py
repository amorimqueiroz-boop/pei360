iimport streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="PEI 360º | Arco AI", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# --- CSS VISUAL (IDENTIDADE ARCO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    :root { --arco-blue: #004e92; --arco-orange: #ff7f00; --input-border: #CBD5E0; --input-bg: #FFFFFF; }
    
    /* Inputs com visual de formulário oficial */
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important; background-color: var(--input-bg) !important; border-radius: 6px !important; color: #2D3748 !important; }
    
    /* Cards do Topo */
    .kpi-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid var(--arco-orange); text-align: center; }
    .kpi-value { font-size: 24px; color: var(--arco-blue); font-weight: 800; }
    .kpi-title { font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; }
    
    /* Botões */
    .stButton>button { background-color: var(--arco-blue); color: white; font-weight: 600; border-radius: 6px; border: none; height: 3em; width: 100%; }
    .stButton>button:hover { background-color: #003a6e; }
    
    /* Cards da Home */
    .home-card { background: #F7FAFC; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .home-card h3 { color: var(--arco-blue); margin-top: 0; margin-bottom: 10px;}
    
    /* Texto de Ajuda */
    .help-text { font-size: 0.9em; color: #4A5568; background-color: #EBF8FF; padding: 10px; border-radius: 5px; border-left: 3px solid #3182CE; margin-bottom: 8px; }
    
    /* Status Visual */
    .status-ok { color: #28a745; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    .status-info { color: #004e92; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GEMINI AI ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ Insira a API Key na barra lateral esquerda para ativar a IA."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Aja como um Especialista em Inclusão Escolar.
        Aluno: {dados['nome']}, Série: {dados['serie']}.
        Hiperfoco: {dados['hiperfoco']}.
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}.
        
        Gere sugestões práticas para o professor:
        1. Como usar o hiperfoco ({dados['hiperfoco']}) para engajar o aluno?
        2. Adaptações de Acesso (Ambiente/Material) específicas para as barreiras citadas.
        3. Adaptações Curriculares (Conteúdo/Avaliação) recomendadas.
        Seja direto, empático e técnico.
        """
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e: return None, f"Erro IA: {str(e)}"

# --- GERADOR WORD ---
def gerar_docx_final(dados):
    doc = Document()
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO E CONTEXTO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    
    # Lógica do Laudo no Documento
    tipo_diag = "Diagnóstico Clínico (Laudo)" if dados['tem_laudo'] else "Hipótese Diagnóstica (Em investigação)"
    doc.add_paragraph(f"{tipo_diag}: {dados['diagnostico']}")
    
    if dados['historico']: 
        doc.add_heading('Histórico Escolar:', level=2)
        doc.add_paragraph(dados['historico'])
    if dados['familia']: 
        doc.add_heading('Escuta da Família:', level=2)
        doc.add_paragraph(dados['familia'])

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

    doc.add_heading('3. PLANO DE AÇÃO E ESTRATÉGIAS', level=1)
    
    # Seção da IA (Consultoria)
    if dados['ia_sugestao']:
        doc.add_heading('Consultoria da Inteligência Artificial:', level=2)
        doc.add_paragraph(dados['ia_sugestao'])
    
    # Seção Manual (Obrigatória)
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

# --- ESTADO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'tem_laudo': False, 'diagnostico': '', 'equipe_externa': [], 
        'historico': '', 'familia': '', 'hiperfoco': '', 
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [], 
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- INTERFACE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    st.markdown("### 🤖 Configuração IA")
    api_key = st.text_input("Cole a API Key do Gemini:", type="password")
    if not api_key: st.warning("Necessário para aba 'Consultoria IA'")
    st.markdown("---")
    st.info("Sistema v4.0 Platinum")

st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 10px; border-radius:15px;'>AI EDITION</span>", unsafe_allow_html=True)

# Abas reestruturadas conforme pedido
abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "🤖 Consultoria IA", "✅ Plano de Ação", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# === ABA 1: HOME (2 CARDS) ===
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h3>📘 O que é o PEI e sua Importância</h3>
            <p>O <b>Plano de Ensino Individualizado (PEI)</b> é a ferramenta que materializa a inclusão. Ele não é apenas um documento burocrático, mas o planejamento estratégico que garante o direito de aprender.</p>
            <p><b>Por que é vital?</b></p>
            <ul>
                <li>Muda o foco da "doença" para a "potência".</li>
                <li>Registra as adaptações (segurança jurídica).</li>
                <li>Orienta o professor em sala de aula.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h3>⚖️ Legislação Vigente (2025)</h3>
            <p>Este sistema está em total conformidade com o <b>Decreto nº 12.773/2025</b>, que atualizou a Política Nacional de Educação Especial.</p>
            <div style="background:white; padding:15px; border-left:4px solid #004e92; margin-top:10px; font-style:italic; font-size:0.95em;">
            "Art. 12. As instituições de ensino devem elaborar plano individualizado... garantindo adaptações razoáveis... independentemente de laudo médico específico."
            </div>
            <p style="margin-top:10px;">O sistema também atende à <b>LBI (Lei 13.146)</b> e <b>Resolução CNE/CP nº 1</b>.</p>
        </div>
        """, unsafe_allow_html=True)

# === ABA 2: IDENTIFICAÇÃO ===
with tab2:
    st.markdown("### 1. Dados Cadastrais")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome Completo do Estudante", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento")
    st.session_state.dados['escola'] = c1.text_input("Escola / Unidade", st.session_state.dados['escola'])
    st.session_state.dados['serie'] = c2.selectbox("Série / Ano", ["Educação Infantil", "Fund I (1º ao 5º)", "Fund II (6º ao 9º)", "Ensino Médio"])
    
    st.markdown("---")
    st.markdown("### 2. Contexto Clínico")
    # Lógica do Laudo
    col_laudo, col_diag = st.columns([1, 2])
    with col_laudo:
        st.write("") 
        st.write("") 
        st.session_state.dados['tem_laudo'] = st.checkbox("Possui Laudo Médico Fechado?")
    with col_diag:
        label_diag = "Diagnóstico Clínico (CID)" if st.session_state.dados['tem_laudo'] else "Hipótese de Diagnóstico (Em investigação)"
        st.session_state.dados['diagnostico'] = st.text_input(label_diag, st.session_state.dados['diagnostico'])

    st.markdown("---")
    st.markdown("### 3. Contexto Escolar e Familiar")
    
    c_h, c_f = st.columns(2)
    with c_h:
        st.markdown('<div class="help-text">💡 <b>O que preencher:</b> Escolas anteriores, histórico de retenção, se já teve mediação, como foi a adaptação nos anos anteriores.</div>', unsafe_allow_html=True)
        st.session_state.dados['historico'] = st.text_area("Histórico Escolar", height=150, placeholder="Descreva aqui a trajetória escolar...")
    
    with c_f:
        st.markdown('<div class="help-text">💡 <b>O que preencher:</b> Rotina de sono/alimentação, expectativas da família, o que eles relatam que funciona em casa para acalmar ou ensinar.</div>', unsafe_allow_html=True)
        st.session_state.dados['familia'] = st.text_area("Relato da Família", height=150, placeholder="Descreva aqui a escuta da família...")

# === ABA 3: MAPEAMENTO ===
with tab3:
    st.info("Mapeie as potências para usar como alavanca e as barreiras para eliminar.")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("### 🌟 Potencialidades")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco (Interesse Intenso)", placeholder="Ex: Dinossauros, Trens, Games...")
        
        opcoes_pot = ["Memória Visual", "Facilidade com Tecnologia", "Habilidade Artística/Desenho", "Boa Oralidade", "Raciocínio Lógico", "Habilidade Musical", "Vínculo Afetivo Fácil"]
        st.session_state.dados['potencias'] = st.multiselect("Habilidades Fortes", opcoes_pot)
        
        st.markdown("**Nível de Engajamento**")
        eng = st.select_slider("", ["Baixo (Passivo)", "Médio (Requer Mediação)", "Alto (Participativo)"], value="Médio (Requer Mediação)"); st.session_state.dados['nivel_engajamento'] = eng
    
    with c2:
        st.markdown("### 🚧 Barreiras de Acesso")
        with st.expander("Sensorial e Físico", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", ["Hipersensibilidade Auditiva", "Busca Sensorial (Toca tudo)", "Agitação Motora", "Baixa Visão", "Dificuldade Motora Fina"])
        with st.expander("Cognitivo e Aprendizagem"):
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", ["Tempo de Atenção Curto", "Não copia do quadro", "Dificuldade de Leitura", "Rigidez Cognitiva"])
        with st.expander("Social e Comportamento"):
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", ["Isolamento Social", "Comportamento Opositor", "Pouca comunicação verbal", "Ecolalia"])
            
        st.markdown("**Nível de Suporte**")
        sup = st.select_slider("", ["Leve (Adaptações)", "Moderado (Monitoria)", "Elevado (AT/Cuidador)"], value="Leve (Adaptações)"); st.session_state.dados['nivel_suporte'] = sup

# === ABA 4: CONSULTORIA IA ===
with tab4:
    c_ia1, c_ia2 = st.columns([1, 2])
    with c_ia1:
        st.markdown("### 🤖 Consultor Virtual")
        st.info("A IA analisará o perfil mapeado e sugerirá caminhos pedagógicos.")
        if st.button("✨ Gerar Consultoria com Gemini"):
            with st.spinner("Analisando perfil do aluno..."):
                res, err = consultar_ia(api_key, st.session_state.dados)
                if err: st.error(err)
                else: st.session_state.dados['ia_sugestao'] = res; st.success("Consultoria Gerada!")
    
    with c_ia2:
        st.markdown("### Resultado da Análise")
        st.session_state.dados['ia_sugestao'] = st.text_area("Sugestões da IA (Você pode editar antes de imprimir):", st.session_state.dados['ia_sugestao'], height=400)

# === ABA 5: PLANO DE AÇÃO (MANUAL) ===
with tab5:
    st.markdown("### ✅ Definição das Estratégias Oficiais")
    st.caption("Selecione abaixo as adaptações que a escola se compromete a realizar.")
    
    c_acao1, c_acao2 = st.columns(2)
    with c_acao1:
        st.markdown("""<div class="kpi-card" style="text-align:left; border-left: 5px solid #004e92;"><h4>Adaptações de Acesso</h4><p style="font-size:0.8em">Mudanças no ambiente ou material (COMO aprende).</p></div>""", unsafe_allow_html=True)
        st.write("")
        opcoes_acesso = ["Tempo estendido para avaliações", "Ledor e Escriba", "Material ampliado (Fonte 14+)", "Uso de Tablet/Tecnologia", "Sentar próximo ao professor", "Uso de Abafadores de Ruído", "Pausas ativas permitidas"]
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Selecione as adaptações de acesso:", options=opcoes_acesso)
        
    with c_acao2:
        st.markdown("""<div class="kpi-card" style="text-align:left; border-left: 5px solid #28a745;"><h4>Adaptações Curriculares</h4><p style="font-size:0.8em">Mudanças no conteúdo ou objetivos (O QUE aprende).</p></div>""", unsafe_allow_html=True)
        st.write("")
        opcoes_curriculo = ["Redução do número de questões", "Priorização de conteúdo essencial", "Avaliação Oral", "Prova Adaptada (Objetiva)", "Atividade Prática em vez de escrita", "Currículo Funcional"]
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Selecione as adaptações curriculares:", options=opcoes_curriculo)

# === ABA 6: EXPORTAR ===
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Preencha o nome do aluno na aba 'Identificação'.")
    else:
        st.success("✅ Documento Oficial Compilado!")
        st.markdown("O arquivo contém: Identificação, Histórico, Mapeamento, Consultoria da IA e o Plano de Ação definido.")
        
        doc_file = gerar_docx_final(st.session_state.dados)
        st.download_button(
            label="📥 BAIXAR PEI COMPLETO (.DOCX)",
            data=doc_file,
            file_name=f"PEI_{st.session_state.dados['nome'].strip()}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    st.markdown("</div>", unsafe_allow_html