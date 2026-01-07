import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from openai import OpenAI

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Arco Inclusão",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (DESIGN SYSTEM ARCO/COC) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    /* Variáveis de Cor */
    :root { 
        --arco-blue: #004e92; 
        --arco-light: #E3F2FD;
        --success-green: #38A169;
    }
    
    /* Inputs Estilizados */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important;
        border: 1px solid #CBD5E0 !important;
    }
    
    /* Sliders Amigáveis */
    div[data-baseweb="slider"] { margin-top: 15px; }

    /* Cards da Home */
    .info-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid var(--arco-blue);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 100%;
        transition: transform 0.2s;
    }
    .info-card:hover { transform: translateY(-3px); }
    .info-card h4 { color: var(--arco-blue); margin-bottom: 10px; font-weight: 700; }
    .info-card p { font-size: 0.9rem; color: #4A5568; line-height: 1.5; }

    /* Botão Principal */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        border-radius: 10px;
        font-weight: 600;
        height: 3.5rem;
        width: 100%;
        border: none;
    }
    .stButton>button:hover { background-color: #003a6e; }
    
    /* Headers */
    h1, h2, h3 { color: #1A202C; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO INTEELIGÊNCIA (DEEPSEEK V3) ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ A chave de API não foi detectada. Verifique o menu lateral."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        prompt_sistema = """
        Você é um Assistente Pedagógico Especialista em Inclusão Escolar (PEI) da rede COC/Arco.
        Seu tom é colaborativo, técnico (mas acessível) e focado em soluções.
        
        DIRETRIZES:
        1. LEGISLAÇÃO: Baseie-se na Lei 13.146 (LBI) e Decreto 10.502. O foco é remover barreiras.
        2. NEUROCIÊNCIA: Use termos como Funções Executivas, Regulação Sensorial e Neuroplasticidade.
        3. FORMATO: Responda com tópicos claros, emojis para organizar e sugestões "mão na massa".
        """
        
        prompt_usuario = f"""
        Olá, preciso de ajuda para estruturar o PEI deste aluno:
        
        👤 ALUNO: {dados['nome']} ({dados['serie']})
        🏥 DIAGNÓSTICO: {dados['diagnostico']}
        🚀 HIPERFOCO (Interesse): {dados['hiperfoco']}
        
        📊 MAPEAMENTO DE BARREIRAS & SUPORTE:
        - Sensorial: {', '.join(dados['b_sensorial'])} (Nível de Suporte: {dados['sup_sensorial']})
        - Cognitivo: {', '.join(dados['b_cognitiva'])} (Nível de Suporte: {dados['sup_cognitiva']})
        - Social: {', '.join(dados['b_social'])} (Nível de Suporte: {dados['sup_social']})
        
        📝 PLANO JÁ ESBOÇADO PELA ESCOLA:
        - Acesso: {', '.join(dados['estrategias_acesso'])}
        - Currículo: {', '.join(dados['estrategias_curriculo'])}
        
        O QUE PRECISO DE VOCÊ (IA):
        1. Como potencializar o aprendizado usando o Hiperfoco "{dados['hiperfoco']}"?
        2. Analise as barreiras citadas e sugira 2 novas tecnologias ou adaptações ambientais.
        3. Uma estratégia prática de avaliação para contornar a dificuldade cognitiva principal.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7,
            stream=False
        )
        return response.choices[0].message.content, None
        
    except Exception as e:
        return None, f"Erro de conexão com DeepSeek: {str(e)}"

# --- GERADOR DE DOCUMENTO DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    # Cabeçalho
    titulo = doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Ano Letivo: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    # 1. Identificação
    doc.add_heading('1. IDENTIFICAÇÃO DO ESTUDANTE', level=1)
    p = doc.add_paragraph()
    p.add_run(f"Nome: ").bold = True; p.add_run(dados['nome'])
    p.add_run(f" | Série: ").bold = True; p.add_run(dados['serie'])
    p.add_run(f"\nDiagnóstico: ").bold = True; p.add_run(dados['diagnostico'])
    
    # 2. Perfil
    doc.add_heading('2. PERFIL DE APRENDIZAGEM', level=1)
    doc.add_paragraph(f"Hiperfoco/Interesse: {dados['hiperfoco']}", style='List Bullet')
    for pot in dados['potencias']: doc.add_paragraph(f"Potencialidade: {pot}", style='List Bullet')
    
    doc.add_heading('Barreiras e Nível de Suporte:', level=2)
    if dados['b_sensorial']: doc.add_paragraph(f"Sensorial ({dados['sup_sensorial']}): {', '.join(dados['b_sensorial'])}")
    if dados['b_cognitiva']: doc.add_paragraph(f"Cognitivo ({dados['sup_cognitiva']}): {', '.join(dados['b_cognitiva'])}")
    if dados['b_social']: doc.add_paragraph(f"Social ({dados['sup_social']}): {', '.join(dados['b_social'])}")

    # 3. Plano
    doc.add_heading('3. ESTRATÉGIAS PEDAGÓGICAS', level=1)
    doc.add_heading('Adaptações de Acesso (Ambiente/Recursos):', level=2)
    for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    
    doc.add_heading('Adaptações Curriculares (Conteúdo/Avaliação):', level=2)
    for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    # 4. IA
    if dados['ia_sugestao']:
        doc.add_heading('4. ORIENTAÇÕES DO ASSISTENTE ESPECIALISTA', level=1)
        doc.add_paragraph(dados['ia_sugestao'])

    doc.add_paragraph('\n___________________________\nAssinatura do Responsável Pedagógico')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO DA SESSÃO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'escola': '', 
        'tem_laudo': False, 'diagnostico': '', 'historico': '', 'familia': '', 'hiperfoco': '', 
        'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    st.markdown("### ⚙️ Configuração")
    
    # Cofre Automático
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Ativa (Cofre)")
    else:
        api_key = st.text_input("Chave API DeepSeek:", type="password")

    st.markdown("---")
    st.info("Versão 6.0 | Arco Inclusão")

# --- CABEÇALHO ---
st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 12px; border-radius:15px; font-weight:600;'>SYSTEM</span>", unsafe_allow_html=True)

# --- NAVEGAÇÃO REORGANIZADA ---
abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "✅ Plano de Ação", "🤖 Assistente de IA", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# ABA 1: HOME (4 CARDS)
with tab1:
    st.markdown("### Bem-vindo ao Sistema de Inclusão Inteligente")
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="info-card">
            <h4>📘 O que é o PEI?</h4>
            <p>O Plano de Ensino Individualizado é o documento vivo que mapeia as barreiras de aprendizagem e define as estratégias para superá-las. Não é sobre facilitar, é sobre <b>acessibilizar</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown("""
        <div class="info-card">
            <h4>⚖️ Obrigatoriedade Legal</h4>
            <p>Em conformidade com a <b>LBI (Lei 13.146)</b> e o <b>Decreto 10.502</b>, as escolas devem garantir adaptações razoáveis. A recusa ou a cobrança extra configuram discriminação.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h4>🧠 Neurociência Aplicada</h4>
            <p>Nossa metodologia foca nas <b>Funções Executivas</b>. Entendemos o perfil cognitivo único de cada aluno para propor intervenções baseadas em evidências científicas.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        st.markdown("""
        <div class="info-card">
            <h4>🤝 Parceria Família-Escola</h4>
            <p>Um PEI de sucesso nasce da escuta ativa. Utilize os dados da anamnese familiar para alinhar expectativas e criar uma rede de apoio consistente.</p>
        </div>
        """, unsafe_allow_html=True)

# ABA 2: ALUNO
with tab2:
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    st.session_state.dados['serie'] = c2.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"])
    st.markdown("---")
    c3, c4 = st.columns([1, 2])
    st.session_state.dados['tem_laudo'] = c3.checkbox("Possui Laudo Médico?")
    st.session_state.dados['diagnostico'] = c4.text_input("Diagnóstico ou Hipótese", st.session_state.dados['diagnostico'], placeholder="Ex: TEA Nível 1, TDAH, Dislexia...")
    
    st.markdown("#### 🗣️ Escuta Ativa")
    st.session_state.dados['familia'] = st.text_area("O que a família relatou? (Rotina, Terapias, Expectativas)", height=100)

# ABA 3: MAPEAMENTO COMPLETO (SLIDERS NOVOS)
with tab3:
    st.info("Mapeie as barreiras e defina a intensidade do suporte necessário para cada área.")
    
    # 1. Hiperfoco e Potências
    st.markdown("### 🚀 Potencialidades")
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (A 'Chave Mestra')", placeholder="Ex: Dinossauros, K-Pop, Lego, Futebol...")
    opcoes_potencias = ["Memória Visual Excelente", "Vocabulário Avançado", "Pensamento Lógico-Matemático", "Habilidade Artística/Criativa", "Hiperlexia (Leitura Precoce)", "Empatia/Cuidado com o outro", "Habilidade Tecnológica"]
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", opcoes_potencias)
    
    st.markdown("---")
    st.markdown("### 🚧 Barreiras & Nível de Suporte")
    
    # BARREIRA SENSORIAL
    with st.expander("👁️ Sensorial e Físico (Corpo e Ambiente)", expanded=True):
        col_b, col_s = st.columns([2, 1])
        opcoes_sensorial = ["Hipersensibilidade Auditiva (Barulho)", "Hipersensibilidade Visual (Luz)", "Busca Proprioceptiva (Agitação/Toque)", "Seletividade Alimentar", "Dificuldade Motora Fina (Escrita)", "Hipotonia (Cansaço físico)", "Dificuldade de Rastreio Visual"]
        st.session_state.dados['b_sensorial'] = col_b.multiselect("Selecione as barreiras sensoriais:", options=opcoes_sensorial)
        st.session_state.dados['sup_sensorial'] = col_s.select_slider("Suporte Sensorial:", options=["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    # BARREIRA COGNITIVA
    with st.expander("🧠 Cognitivo (Processamento e Aprendizagem)"):
        col_b, col_s = st.columns([2, 1])
        opcoes_cognitiva = ["Atenção Flutuante/Dispersão", "Memória de Trabalho Reduzida", "Dificuldade de Abstração", "Rigidez Cognitiva (Dificuldade em mudar)", "Lentidão no Processamento", "Dificuldade em Planejamento (Funções Executivas)", "Disgrafia/Disortografia"]
        st.session_state.dados['b_cognitiva'] = col_b.multiselect("Selecione as barreiras cognitivas:", options=opcoes_cognitiva)
        st.session_state.dados['sup_cognitiva'] = col_s.select_slider("Suporte Cognitivo:", options=["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    # BARREIRA SOCIAL
    with st.expander("❤️ Social e Emocional (Interação)"):
        col_b, col_s = st.columns([2, 1])
        opcoes_social = ["Dificuldade na Teoria da Mente (Entender o outro)", "Interpretação Literal (Não entende ironia)", "Baixa Tolerância à Frustração", "Isolamento/Dificuldade em iniciar interação", "Ansiedade de Desempenho", "Desregulação Emocional"]
        st.session_state.dados['b_social'] = col_b.multiselect("Selecione as barreiras sociais:", options=opcoes_social)
        st.session_state.dados['sup_social'] = col_s.select_slider("Suporte Social:", options=["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

# ABA 4: PLANO DE AÇÃO (MOVIDA PARA ANTES DA IA)
with tab4:
    st.markdown("### ✅ Estratégias da Escola")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso (Meios)**")
        opcoes_acesso = ["Tempo estendido (+25% ou +50%)", "Ledor Humano ou Digital", "Escriba", "Material Ampliado (Fonte Arial 24)", "Protetor Auricular/Fone", "Uso de Tablet/Notebook", "Local de prova separado", "Pausas estratégicas"]
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", opcoes_acesso)
    with c2:
        st.markdown("**Adaptações Curriculares (Fins)**")
        opcoes_curriculo = ["Redução do número de questões", "Priorização de Conteúdo Essencial", "Avaliação Oral", "Mapa Mental como Avaliação", "Fragmentação de tarefas", "Enunciados curtos e diretos", "Apoio visual nas questões"]
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", opcoes_curriculo)

# ABA 5: ASSISTENTE DE IA (RENOVADA)
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    
    with col_ia_left:
        st.markdown("### 🤖 Assistente Arco")
        st.markdown("""
        <div style="background-color: #F7FAFC; padding: 15px; border-radius: 10px; border: 1px solid #E2E8F0;">
        <p style="font-size: 0.9rem;"><b>Olá, colega educador!</b></p>
        <p style="font-size: 0.85rem;">Já li o mapeamento que você fez. Posso sugerir conexões entre o hiperfoco do aluno e o conteúdo, além de refinar as adaptações.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("✨ Analisar e Sugerir"):
            if not st.session_state.dados['nome']:
                st.warning("Por favor, preencha o nome do aluno na aba 'Aluno' primeiro.")
            else:
                with st.spinner("Consultando base de Neurociência e LBI..."):
                    res, err = consultar_ia(api_key, st.session_state.dados)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Análise concluída!")
    
    with col_ia_right:
        st.markdown("### 💡 Sugestões do Assistente")
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Copie ou edite as sugestões abaixo:", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.info("Clique no botão ao lado para gerar as sugestões.")

# ABA 6: DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        st.success("✅ Documento pronto para exportação.")
        arquivo = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 Baixar PEI em Word (.docx)", arquivo, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("Preencha os dados do aluno para liberar o download.")
    st.markdown("</div>", unsafe_allow_html=True)