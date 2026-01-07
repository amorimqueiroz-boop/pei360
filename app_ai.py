import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Arco Inclusão",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (DESIGN SYSTEM ARCO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    :root { 
        --arco-blue: #004e92; 
        --arco-light: #E3F2FD;
    }
    
    /* Inputs refinados */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important;
        border: 1px solid #CBD5E0 !important;
    }
    
    /* Destaque para os Sliders */
    div[data-baseweb="slider"] { padding-top: 10px; padding-bottom: 10px; }

    /* Cards Informativos */
    .info-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid var(--arco-blue);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        height: 100%;
        margin-bottom: 15px;
    }
    .info-card h4 { color: var(--arco-blue); margin-bottom: 8px; font-weight: 700; }
    .info-card p { font-size: 0.9rem; color: #4A5568; line-height: 1.4; }
    
    /* Box de Calibragem da IA */
    .ai-tech-card {
        background-color: #2D3748;
        color: #E2E8F0;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        border: 1px solid #4A5568;
        margin-bottom: 20px;
    }

    /* Botões */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        height: 3em;
        width: 100%;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO INTEELIGÊNCIA (DEEPSEEK V3) ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ A chave de API não foi detectada. Verifique o menu lateral."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # PROMPT DE ALTA PRECISÃO
        prompt_sistema = """
        Você é um Assistente Pedagógico Especialista em Inclusão Escolar (PEI) da rede COC/Arco.
        
        CALIBRAGEM DA RESPOSTA:
        - Temperatura: 0.7 (Equilíbrio entre técnica e criatividade).
        - Base Legal: Lei 13.146 (LBI) e Desenho Universal para Aprendizagem (DUA).
        - Foco: Neurociência Educacional (Funções Executivas).
        
        ESTRUTURA DA RESPOSTA:
        Use linguagem acolhedora, tópicos claros e emojis para organização visual.
        """
        
        prompt_usuario = f"""
        Analise este perfil e gere estratégias pedagógicas:
        
        👤 ALUNO: {dados['nome']} ({dados['serie']})
        🏥 DIAGNÓSTICO: {dados['diagnostico']}
        🚀 HIPERFOCO: {dados['hiperfoco']}
        
        📊 BARREIRAS E SUPORTE:
        - Sensorial: {', '.join(dados['b_sensorial'])} (Nível: {dados['sup_sensorial']})
        - Cognitivo: {', '.join(dados['b_cognitiva'])} (Nível: {dados['sup_cognitiva']})
        - Social: {', '.join(dados['b_social'])} (Nível: {dados['sup_social']})
        
        📝 ESTRATÉGIAS JÁ PENSADAS:
        - Acesso: {', '.join(dados['estrategias_acesso'])}
        - Currículo: {', '.join(dados['estrategias_curriculo'])}
        
        SOLICITAÇÃO:
        1. 🧠 Conexão Neural: Como usar o Hiperfoco "{dados['hiperfoco']}" para engajar este aluno nas aulas?
        2. 🛠️ Tecnologia & Ambiente: Sugira 2 recursos práticos para as barreiras citadas.
        3. 🎓 Avaliação Adaptada: Uma forma de avaliar este aluno considerando suas dificuldades cognitivas.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7,
            stream=False
        )
        return response.choices[0].message.content, None
        
    except Exception as e:
        return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    titulo = doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Ano Letivo: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    if dados['historico']: doc.add_paragraph(f"Histórico Escolar: {dados['historico']}")
    if dados['familia']: doc.add_paragraph(f"Relato da Família: {dados['familia']}")
    
    doc.add_heading('2. MAPEAMENTO', level=1)
    doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}")
    for pot in dados['potencias']: doc.add_paragraph(f"Potência: {pot}", style='List Bullet')
    
    doc.add_heading('Barreiras Mapeadas:', level=2)
    if dados['b_sensorial']: doc.add_paragraph(f"Sensorial ({dados['sup_sensorial']}): {', '.join(dados['b_sensorial'])}")
    if dados['b_cognitiva']: doc.add_paragraph(f"Cognitivo ({dados['sup_cognitiva']}): {', '.join(dados['b_cognitiva'])}")
    if dados['b_social']: doc.add_paragraph(f"Social ({dados['sup_social']}): {', '.join(dados['b_social'])}")

    doc.add_heading('3. ESTRATÉGIAS', level=1)
    doc.add_heading('Adaptações de Acesso:', level=2)
    for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    doc.add_heading('Adaptações Curriculares:', level=2)
    for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    if dados['ia_sugestao']:
        doc.add_heading('4. CONSULTORIA ESPECIALISTA (IA)', level=1)
        doc.add_paragraph(dados['ia_sugestao'])

    doc.add_paragraph('\n___________________________\nCoordenação Pedagógica')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO INICIAL ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'serie': None, 'escola': '', 'tem_laudo': False, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Segura Ativada")
    else:
        api_key = st.text_input("Chave API DeepSeek:", type="password")
    st.markdown("---")
    st.info("Versão 6.1 | Português BR")

# --- APP ---
st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 12px; border-radius:15px; font-weight:600;'>SYSTEM</span>", unsafe_allow_html=True)

abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "✅ Plano de Ação", "🤖 Assistente de IA", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME
with tab1:
    st.markdown("### Bem-vindo ao Sistema de Inclusão Inteligente")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="info-card"><h4>📘 O que é o PEI?</h4><p>O Plano de Ensino Individualizado é a ferramenta oficial para eliminar barreiras. Ele transforma a matrícula em inclusão real.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4>⚖️ Legislação (LBI)</h4><p>Baseado na Lei 13.146 e Decreto 10.502. O sistema garante que as adaptações razoáveis sejam registradas.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="info-card"><h4>🧠 Neurociência</h4><p>Foco nas Funções Executivas. Entendemos como o cérebro do aluno aprende para propor o método certo.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4>🤝 Escola & Família</h4><p>A colaboração é vital. Utilize os dados da escuta familiar para alinhar expectativas e criar vínculo.</p></div>', unsafe_allow_html=True)

# 2. ALUNO
with tab2:
    st.info("Preencha os dados básicos para iniciar o dossiê do estudante.")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'], placeholder="Digite o nome completo")
    st.session_state.dados['serie'] = c2.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione a série...")
    
    st.markdown("---")
    c3, c4 = st.columns([1, 2])
    st.session_state.dados['tem_laudo'] = c3.checkbox("Possui Laudo Médico?")
    st.session_state.dados['diagnostico'] = c4.text_input("Diagnóstico ou Hipótese", st.session_state.dados['diagnostico'], placeholder="Ex: TEA, TDAH, Dislexia (Se houver)")
    
    st.markdown("---")
    st.markdown("#### 📝 Contexto Completo")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Escolas anteriores, repetências, relação com a aprendizagem...", help="Descreva brevemente a trajetória escolar do aluno até aqui.")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="Relato dos pais, rotina em casa, terapias...", help="Quais são as expectativas e percepções da família sobre o aluno?")

# 3. MAPEAMENTO
with tab3:
    st.info("💡 Identifique as potências para superar as barreiras.")
    
    st.markdown("### 🚀 Potencialidades")
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)", placeholder="O que o aluno AMA? (Ex: Minecraft, Música)", help="Use isso como alavanca de engajamento.")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes/Desenho", "Oralidade", "Lógica", "Empatia", "Esportes"], placeholder="Selecione as habilidades...")
    
    st.markdown("---")
    st.markdown("### 🚧 Barreiras e Nível de Suporte")
    
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Quais são as barreiras?", ["Hipersensibilidade (Barulho/Luz)", "Busca Sensorial (Agitação)", "Seletividade Alimentar", "Dificuldade Motora"], placeholder="Selecione...")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Intensidade do Suporte Sensorial:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    with st.expander("🧠 Cognitivo e Aprendizagem"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Quais são as barreiras?", ["Atenção Dispersa", "Memória Curta", "Rigidez de Pensamento", "Lentidão no Processamento", "Dificuldade de Abstração"], placeholder="Selecione...")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Intensidade do Suporte Cognitivo:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    with st.expander("❤️ Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Quais são as barreiras?", ["Isolamento", "Baixa Frustração", "Interpretação Literal", "Ansiedade"], placeholder="Selecione...")
        st.session_state.dados['sup_social'] = st.select_slider("Intensidade do Suporte Social:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

# 4. PLANO DE AÇÃO
with tab4:
    st.markdown("### ✅ Definição de Estratégias")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso (O Meio)**", help="Mudanças no ambiente, material ou tempo.")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Selecione os recursos:", ["Tempo estendido", "Ledor/Escriba", "Material Ampliado", "Uso de Tablet", "Local Silencioso", "Pausas Ativas"], placeholder="Selecione as adaptações...")
    with c2:
        st.markdown("**Adaptações Curriculares (O Fim)**", help="Mudanças na forma de ensinar ou avaliar o conteúdo.")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Selecione as estratégias:", ["Redução de Questões", "Prova Oral", "Mapa Mental", "Conteúdo Prioritário", "Atividade Prática"], placeholder="Selecione as adaptações...")

# 5. ASSISTENTE IA
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    
    with col_ia_left:
        st.markdown("### 🤖 Configuração do Assistente")
        st.markdown("""
        <div class="ai-tech-card">
        <b>⚙️ PAINEL DE CALIBRAGEM</b><br>
        -------------------------<br>
        MODELO: DeepSeek V3 (High-Reasoning)<br>
        TEMPERATURA: 0.7 (Criativo + Técnico)<br>
        BASE: LBI 13.146 + Neurociência<br>
        STATUS: <span style="color:#48BB78">Online</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("A IA analisará o mapeamento (Aba 3) e o plano (Aba 4) para sugerir melhorias.")
        
        if st.button("✨ Gerar Consultoria"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome do aluno primeiro.")
            else:
                with st.spinner("Processando dados neurofuncionais..."):
                    res, err = consultar_ia(api_key, st.session_state.dados)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Análise concluída!")

    with col_ia_right:
        st.markdown("### 💡 Parecer Técnico")
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Sugestões do Assistente:", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.markdown("*O resultado da análise aparecerá aqui.*")

# 6. DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        doc_file = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 Baixar PEI Completo (.docx)", doc_file, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("Preencha os dados do aluno para liberar o download.")
    st.markdown("</div>", unsafe_allow_html=True)