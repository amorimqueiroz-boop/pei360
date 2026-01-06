import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- 1. CONFIGURAÇÃO E ESTILO (DESIGN SYSTEM ARCO) ---
st.set_page_config(
    page_title="PEI 360 | Arco Educação",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Paleta de Cores Arco Educação & Acessibilidade */
    :root {
        --arco-blue: #004e92;       /* Azul Institucional */
        --arco-orange: #ff7f00;     /* Laranja Destaque */
        --bg-gray: #f8f9fa;         /* Fundo Suave */
        --text-dark: #2c3e50;
    }
    
    .main {background-color: var(--bg-gray);}
    
    /* Tipografia */
    h1, h2, h3 {color: var(--arco-blue); font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 700;}
    p {color: var(--text-dark); font-size: 1.1rem;}
    
    /* Cards Informativos (Home) */
    .edu-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 6px solid var(--arco-blue);
        margin-bottom: 20px;
    }
    .lei-card {
        background-color: #e3f2fd; /* Azul bem claro */
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #bbdefb;
        color: #0d47a1;
        font-style: italic;
    }
    
    /* Botões Premium */
    .stButton>button {
        background-color: var(--arco-blue);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #003366; /* Azul mais escuro no hover */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Ajustes de Sliders e Inputs */
    .stSlider > div > div > div > div {background-color: var(--arco-orange);}
    .stTextArea textarea {font-size: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE GERAÇÃO DO WORD (LÓGICA PEDAGÓGICA) ---
def gerar_docx_especialista(dados):
    doc = Document()
    
    # Cabeçalho Institucional
    titulo = doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(f'Instituição: {dados["escola"]} | Ano Letivo: {date.today().year}')
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Identificação e Histórico
    doc.add_heading('1. IDENTIFICAÇÃO E CONTEXTO', level=1)
    
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False 
    celulas = tbl.rows[0].cells
    celulas[0].text = f"Estudante: {dados['nome']}\nNascimento: {str(dados['nasc']) if dados['nasc'] else '--'}"
    celulas[1].text = f"Série/Ano: {dados['serie']}\nTurma/Turno: {dados['turma']}"
    
    doc.add_paragraph(f"\nDiagnóstico Clínico (CID): {dados['cid']}")
    doc.add_paragraph(f"Equipe Multidisciplinar Externa: {', '.join(dados['equipe_externa']) if dados['equipe_externa'] else 'Não possui acompanhamento externo declarado.'}")
    
    doc.add_heading('Histórico Escolar Breve:', level=2)
    doc.add_paragraph(dados['historico'] if dados['historico'] else "Sem observações de histórico.")

    doc.add_heading('Relato da Família (Escuta Ativa):', level=2)
    doc.add_paragraph(dados['familia'] if dados['familia'] else "Não houve registro de entrevista familiar.")

    # 2. Perfil do Estudante (O Coração do PEI)
    doc.add_heading('2. PERFIL DO ESTUDANTE (ESTUDO DE CASO)', level=1)
    
    # Indicadores Visuais em Texto
    p_ind = doc.add_paragraph()
    p_ind.add_run(f"Nível de Suporte Geral: {dados['nivel_suporte']}").bold = True
    doc.add_paragraph(f"• Engajamento: {dados['nivel_engajamento']}")
    doc.add_paragraph(f"• Autonomia (AVDs): {dados['nivel_autonomia']}")

    doc.add_heading('Potencialidades e Hiperfocos (Alavancas):', level=2)
    if dados['hiperfoco']:
        p_hip = doc.add_paragraph()
        p_hip.add_run("Hiperfoco/Interesse Restrito: ").bold = True
        p_hip.add_run(dados['hiperfoco'])
    
    if dados['potencias']:
        for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')

    doc.add_heading('Mapeamento de Barreiras:', level=2)
    
    if dados['b_sensorial']: 
        p = doc.add_paragraph(); p.add_run("Barreiras Sensoriais e Físicas:").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    
    if dados['b_cognitiva']: 
        p = doc.add_paragraph(); p.add_run("Barreiras Cognitivas e de Aprendizagem:").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
        
    if dados['b_social']: 
        p = doc.add_paragraph(); p.add_run("Barreiras Sociais e de Comunicação:").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Plano de Intervenção
    doc.add_heading('3. ORGANIZAÇÃO DO TRABALHO PEDAGÓGICO', level=1)
    
    doc.add_heading('Adaptações de Acesso (Como o aluno aprende):', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Nenhuma adaptação de acesso necessária no momento.")
        
    doc.add_heading('Adaptações Curriculares (O que o aluno aprende):', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')
    else: doc.add_paragraph("Segue o currículo padrão da série.")

    doc.add_paragraph('\n\n___________________________________\nCoordenação Pedagógica')
    doc.add_paragraph('\n___________________________________\nResponsável Legal / Família')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. DICIONÁRIO DE DADOS (SESSION STATE) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 
        'cid': '', 'equipe_externa': [], 
        'historico': '', 'familia': '', # Campos Restaurados
        'hiperfoco': '', # Campo Novo
        'nivel_suporte': 'Nível 1: Leve (Apenas adaptações)',
        'nivel_engajamento': 'Médio (Requer mediação)',
        'nivel_autonomia': 'Com Supervisão Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# --- 4. INTERFACE DO USUÁRIO ---

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=160)
    st.markdown("### PEI 360°")
    st.caption("Sistema de Gestão Inclusiva")
    st.markdown("---")
    st.success("✅ **Status:** Sistema Online")
    st.info("Utilize as abas superiores para navegar entre a fundamentação legal e o preenchimento do plano.")

# Título Principal
st.title("Gestão de PEI e Inclusão Escolar")

# Abas de Navegação (Fluxo Lógico)
tab_home, tab_ident, tab_mapa, tab_plano, tab_export = st.tabs([
    "🏠 Fundamentação & Lei", 
    "👤 Identificação", 
    "🔍 Mapeamento (Estudo)", 
    "🛠️ Estratégias", 
    "🖨️ Finalizar Documento"
])

# === ABA 1: HOME PAGE (EDUCATIVA & AUTORIDADE) ===
with tab_home:
    st.header("Por que o PEI é essencial?")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        <div class="edu-card">
        <h3>📘 O que é o PEI?</h3>
        <p>O <b>Plano de Ensino Individualizado (PEI)</b> é o instrumento pedagógico que transforma o direito à educação em prática.</p>
        <p>Ele substitui a lógica médica (focada na doença) pela <b>lógica pedagógica</b> (focada em remover barreiras).</p>
        <p><b>Não é apenas burocracia:</b> É o planejamento estratégico da escola para garantir que o aluno aprenda.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown("""
        <div class="edu-card">
        <h3>⚖️ Legislação Atualizada (2025)</h3>
        <p>A conformidade deste sistema baseia-se em:</p>
        <div class="lei-card">
        <b>1. Decreto nº 12.773 (Dez/2025):</b><br>
        "Art. 12. As instituições devem elaborar plano individualizado... independentemente de laudo médico."
        </div>
        <div style="margin-top: 10px;" class="lei-card">
        <b>2. Lei Brasileira de Inclusão (LBI):</b><br>
        Garante o desenho universal e adaptações razoáveis como direito, não favor.
        </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.info("👉 **Como usar:** Clique na aba **'Identificação'** acima para iniciar um novo Estudo de Caso.")

# === ABA 2: IDENTIFICAÇÃO E HISTÓRICO ===
with tab_ident:
    st.subheader("1. Dados Cadastrais e Contexto")
    
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.dados['nome'] = st.text_input("Nome Completo do Estudante", value=st.session_state.dados['nome'])
        st.session_state.dados['nasc'] = st.date_input("Data de Nascimento")
        st.session_state.dados['escola'] = st.text_input("Unidade Escolar (COC)", value=st.session_state.dados['escola'])
    with c2:
        st.session_state.dados['serie'] = st.selectbox("Série/Ano Escolar", ["Ed. Infantil", "Fund I (1º ao 5º)", "Fund II (6º ao 9º)", "Ensino Médio"])
        st.session_state.dados['turma'] = st.text_input("Turma (Ex: 3º B)")
        st.session_state.dados['cid'] = st.text_input("Diagnóstico Clínico (Se houver) ou Hipótese")

    st.markdown("---")
    st.subheader("2. Histórico e Família")
    
    col_hist1, col_hist2 = st.columns(2)
    with col_hist1:
        st.markdown("**Breve Histórico Escolar:**")
        st.caption("O aluno frequentou outras escolas? Teve retenção? Como foi a adaptação anterior?")
        st.session_state.dados['historico'] = st.text_area("Digite o histórico aqui...", height=100, key="hist_input")
        
    with col_hist2:
        st.markdown("**Relato da Família (Escuta):**")
        st.caption("Quais as expectativas da família? O que eles relatam que funciona em casa?")
        st.session_state.dados['familia'] = st.text_area("Digite o relato da família aqui...", height=100, key="fam_input")

    st.markdown("---")
    st.markdown("**Rede de Apoio Externa**")
    st.session_state.dados['equipe_externa'] = st.multiselect(
        "Quais profissionais atendem o aluno fora da escola?",
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psiquiatra Infantil", "Psicopedagogo"]
    )

# === ABA 3: MAPEAMENTO PEDAGÓGICO ===
with tab_mapa:
    st.markdown("""
    <div class="lei-card">
    💡 <b>Conceito Importante:</b> No PEI, não listamos "sintomas". Listamos <b>Barreiras</b> (o que o ambiente impõe) e <b>Potências</b> (o que o aluno usa para superar).
    </div>
    """, unsafe_allow_html=True)
    
    c_pot, c_bar = st.columns([1, 1])

    with c_pot:
        st.markdown("### 🌟 Potencialidades")
        
        # CAMPO DE HIPERFOCO SEPARADO
        st.markdown("**Hiperfoco / Interesse Restrito:**")
        st.caption("Tema de interesse intenso que serve como porta de entrada para o vínculo (Ex: Dinossauros, Trens, Mapas).")
        st.session_state.dados['hiperfoco'] = st.text_input("Qual o hiperfoco do aluno?", placeholder="Ex: Minecraft, Astronomia...")

        st.markdown("**Habilidades Gerais:**")
        st.session_state.dados['potencias'] = st.multiselect("Selecione os pontos fortes:", 
            ["Memória Visual", "Facilidade com Tecnologia", "Habilidade Artística/Desenho", 
             "Boa Oralidade", "Raciocínio Lógico", "Habilidade Musical", "Desempenho Motor/Esportes", "Vínculo Afetivo Fácil"])
        
        st.markdown("---")
        st.markdown("#### Indicadores de Desenvolvimento")
        st.session_state.dados['nivel_engajamento'] = st.select_slider(
            "Nível de Engajamento nas Aulas:",
            options=["Baixo (Passivo/Alheio)", "Médio (Requer Mediação)", "Alto (Participativo)", "Oscilante"],
            value="Médio (Requer Mediação)"
        )
        st.session_state.dados['nivel_autonomia'] = st.select_slider(
            "Autonomia (Uso de banheiro, alimentação, materiais):",
            options=["Dependente (Total)", "Com Supervisão Constante", "Com Supervisão Parcial", "Autônomo"],
            value="Com Supervisão Parcial"
        )

    with c_bar:
        st.markdown("### 🚧 Barreiras de Acesso")
        
        with st.expander("1. Sensorial e Físico (Corpo e Ambiente)", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect(
                "Quais barreiras o ambiente impõe?",
                ["Hipersensibilidade Auditiva (Barulho)", "Busca Sensorial (Toca em tudo)", 
                 "Agitação Motora Excessiva", "Baixa Visão", "Baixa Audição", "Dificuldade Motora Fina (Escrita)"]
            )
        with st.expander("2. Cognitivo e Acadêmico (Processamento)"):
            st.session_state.dados['b_cognitiva'] = st.multiselect(
                "Quais barreiras o método impõe?",
                ["Tempo de Atenção Curto", "Dificuldade de Abstração", "Não realiza cópia do quadro", 
                 "Dificuldade de Leitura/Interpretação", "Rigidez Cognitiva (Não aceita errar)"]
            )
        with st.expander("3. Social e Comunicacional (Interação)"):
            st.session_state.dados['b_social'] = st.multiselect(
                "Quais barreiras a convivência impõe?",
                ["Isolamento Social", "Comportamento Opositor", "Pouca Comunicação Verbal", 
                 "Ecolalia (Repetição de falas)", "Dificuldade em entender regras sociais"]
            )
            
        st.markdown("#### Nível de Suporte Geral")
        st.session_state.dados['nivel_suporte'] = st.select_slider(
            "Classificação de Necessidade de Apoio:",
            options=["Nível 1: Leve (Adaptações pontuais)", "Nível 2: Moderado (Monitoria em sala)", "Nível 3: Elevado (Suporte Contínuo/AT)"],
            value="Nível 1: Leve (Adaptações pontuais)"
        )

# === ABA 4: ESTRATÉGIAS (PLANO DE AÇÃO) ===
with tab_plano:
    st.subheader("Planejamento de Intervenções")
    st.info("Aqui definimos COMO a escola vai se adaptar ao aluno, e não o contrário.")
    
    # Sugestões Automáticas Baseadas nas Barreiras
    sugestoes_acesso = []
    if "Hipersensibilidade Auditiva (Barulho)" in st.session_state.dados['b_sensorial']: 
        sugestoes_acesso.append("Uso de fones abafadores em momentos de crise")
        sugestoes_acesso.append("Permitir saída da sala em picos de ruído")
    if "Não realiza cópia do quadro" in st.session_state.dados['b_cognitiva']: 
        sugestoes_acesso.append("Fornecer pauta impressa ou permitir foto da lousa")
    if "Agitação Motora Excessiva" in st.session_state.dados['b_sensorial']:
        sugestoes_acesso.append("Pausas ativas (permissão para dar uma volta)")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="edu-card">
        <b>Adaptações de Acesso</b><br>
        <small>Mudanças no ambiente, material ou forma de comunicação. O conteúdo é o mesmo.</small>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Selecione as estratégias:", 
            options=sugestoes_acesso + ["Tempo Estendido para provas", "Ledor e Escriba", "Material Ampliado", "Sentar próximo ao professor", "Uso de Tablet/Tecnologia"],
            default=sugestoes_acesso
        )
        
    with c2:
        st.markdown("""
        <div class="edu-card">
        <b>Adaptações Curriculares</b><br>
        <small>Mudanças nos objetivos ou conteúdo. Usado quando o acesso não é suficiente.</small>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.dados['estrategias_curriculo'] = st.multiselect(
            "Selecione as estratégias:", 
            ["Redução do número de questões", "Priorização de conteúdo essencial", "Avaliação Oral", "Atividade prática em vez de escrita", "Currículo Funcional"]
        )

# === ABA 5: FINALIZAR E EXPORTAR ===
with tab_export:
    st.header("🖨️ Emissão do Documento Oficial")
    
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Por favor, preencha o **Nome do Estudante** na aba 'Identificação' antes de gerar o documento.")
    else:
        col_d1, col_d2 = st.columns([2, 1])
        
        with col_d1:
            st.success("✅ O PEI foi compilado com sucesso.")
            st.markdown(f"""
            **Resumo do Plano:**
            * **Estudante:** {st.session_state.dados['nome']}
            * **Hiperfoco:** {st.session_state.dados['hiperfoco'] if st.session_state.dados['hiperfoco'] else 'Não informado'}
            * **Barreiras Mapeadas:** {len(st.session_state.dados['b_sensorial']) + len(st.session_state.dados['b_cognitiva']) + len(st.session_state.dados['b_social'])}
            * **Estratégias Definidas:** {len(st.session_state.dados['estrategias_acesso']) + len(st.session_state.dados['estrategias_curriculo'])}
            """)
            
        with col_d2:
            st.markdown("### Baixar Arquivo")
            doc_buffer = gerar_docx_especialista(st.session_state.dados)
            
            st.download_button(
                label="📥 Download PEI (.docx)",
                data=doc_buffer,
                file_name=f"PEI_{st.session_state.dados['nome'].strip().replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.caption("O arquivo gerado é editável no Word para inserção de logotipo e assinaturas.")
