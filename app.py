import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURAÇÃO VISUAL (Identidade Arco Educação) ---
st.set_page_config(
    page_title="PEI 360 | Arco Educação",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional
st.markdown("""
    <style>
    :root {--arco-blue: #004e92; --arco-orange: #ff7f00; --bg-light: #f4f6f9;}
    .main {background-color: var(--bg-light);}
    h1, h2, h3 {color: var(--arco-blue); font-family: 'Helvetica Neue', sans-serif;}
    .stButton>button {background-color: var(--arco-blue); color: white; border-radius: 6px; font-weight: 600;}
    .stExpander {background-color: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}
    .destaque-pedagogico {padding: 15px; background-color: #e3f2fd; border-left: 5px solid #004e92; border-radius: 4px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GERADORA DE WORD (.DOCX) ---
def gerar_docx_completo(dados):
    doc = Document()
    
    # Estilo do Título
    titulo = doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Instituição: {dados["escola"]} | Ano Letivo: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Identificação
    doc.add_heading('1. DADOS DE IDENTIFICAÇÃO E CONTEXTO', level=1)
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False 
    celulas = tbl.rows[0].cells
    celulas[0].text = f"Nome: {dados['nome']}\nNascimento: {dados['nasc']}"
    celulas[1].text = f"Série: {dados['serie']}\nNível de Suporte Estimado: {dados['nivel_suporte']}"
    
    doc.add_paragraph(f"\nLaudo/Hipótese Diagnóstica: {dados['cid']}")
    doc.add_paragraph(f"Equipe Multidisciplinar Externa: {', '.join(dados['equipe_externa']) if dados['equipe_externa'] else 'Não possui.'}")

    # 2. Perfil Pedagógico (Estudo de Caso)
    doc.add_heading('2. PERFIL DO ESTUDANTE (ESTUDO DE CASO)', level=1)
    
    doc.add_heading('Potencialidades e Interesses (Alavancas):', level=2)
    if dados['potencias']:
        for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
    else: doc.add_paragraph("Não informadas.")

    doc.add_heading('Barreiras Identificadas:', level=2)
    doc.add_paragraph("Barreiras Sensoriais/Físicas:", style='Strong')
    if dados['b_sensorial']: 
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    
    doc.add_paragraph("Barreiras Cognitivas/Aprendizagem:", style='Strong')
    if dados['b_cognitiva']: 
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
        
    doc.add_paragraph("Barreiras Sociais/Comunicacionais:", style='Strong')
    if dados['b_social']: 
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Plano de Ação
    doc.add_heading('3. ORGANIZAÇÃO DO TRABALHO PEDAGÓGICO', level=1)
    
    doc.add_heading('Adaptações de Acesso (Como ensinamos):', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
        
    doc.add_heading('Adaptações Curriculares (O que ensinamos):', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    # 4. Avaliação
    doc.add_heading('4. SISTEMA DE AVALIAÇÃO', level=1)
    doc.add_paragraph("A avaliação será processual, descritiva e focada na evolução individual do estudante em relação ao seu ponto de partida (Art. 24 LDB).")
    
    doc.add_paragraph('\n\n___________________________________\nAssinatura da Coordenação / Direção')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- SIDEBAR: ESTADO DO APP ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=150) # Logo genérico placeholder
    st.title("PEI 360°")
    st.info("Ferramenta de elaboração de Plano de Ensino Individualizado em conformidade com o Decreto 12.773/2025.")
    progresso = st.progress(0)

# --- CABEÇALHO ---
st.title("Gestão de PEI e Inclusão Escolar")
st.markdown("Preencha as abas sequencialmente para gerar o documento oficial.")

# --- ABAS DE NAVEGAÇÃO ---
tab1, tab2, tab3, tab4 = st.tabs(["1. Aluno & Contexto", "2. Mapeamento Profundo", "3. Definição de Estratégias", "4. Documento Final"])

# --- DICIONÁRIO DE DADOS (SESSION STATE) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'escola': '', 'cid': '',
        'equipe_externa': [], 'nivel_suporte': '',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# === ABA 1: IDENTIFICAÇÃO ===
with tab1:
    st.subheader("📝 Identificação e Contexto")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.dados['nome'] = st.text_input("Nome Completo do Estudante", value=st.session_state.dados['nome'])
        st.session_state.dados['nasc'] = st.date_input("Data de Nascimento")
        st.session_state.dados['escola'] = st.text_input("Unidade Escolar (COC)", value=st.session_state.dados['escola'])
    with col2:
        st.session_state.dados['serie'] = st.selectbox("Ano/Série Atual", ["Ed. Infantil", "Fund I (1º-5º)", "Fund II (6º-9º)", "Ensino Médio"])
        st.session_state.dados['cid'] = st.text_input("Diagnóstico (CID) ou Hipótese (Se houver)")
        st.session_state.dados['equipe_externa'] = st.multiselect("Apoio Externo (Rede de Proteção):", ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neurologista", "Psiquiatra"])

    st.markdown("---")
    st.subheader("Nível de Suporte (Classificação Pedagógica)")
    st.markdown("""
    *Baseado na necessidade de terceiros para realizar atividades escolares.*
    """)
    st.session_state.dados['nivel_suporte'] = st.select_slider(
        "Selecione o nível de suporte necessário:",
        options=["Nível 1: Leve (Apenas adaptações)", "Nível 2: Moderado (Monitoria parcial)", "Nível 3: Elevado (Suporte contínuo/AT)"]
    )

# === ABA 2: MAPEAMENTO (O RETORNO DOS CAMPOS DETALHADOS) ===
with tab2:
    st.markdown('<div class="destaque-pedagogico">💡 <b>O Estudo de Caso:</b> Não foque no que falta (déficit), mas em como o ambiente impacta o aluno.</div>', unsafe_allow_html=True)
    
    col_pot, col_bar = st.columns([1, 2])
    
    with col_pot:
        st.subheader("🌟 Potencialidades")
        st.caption("Alavancas para engajamento")
        st.session_state.dados['potencias'] = st.multiselect(
            "Selecione:",
            ["Memória Visual", "Interesse em Tecnologia", "Habilidade Artística/Desenho", 
             "Hiperfoco (Dinossauros, Trens, Games)", "Boa Oralidade", "Afetividade/Vínculo Fácil",
             "Raciocínio Lógico-Matemático", "Habilidade Musical", "Esportes/Motor Grosso"]
        )

    with col_bar:
        st.subheader("🚧 Barreiras de Acesso (Mapeamento)")
        
        with st.expander("1. Sensorial e Físico (Corpo e Ambiente)"):
            st.session_state.dados['b_sensorial'] = st.multiselect(
                "Desafios observados:",
                ["Hipersensibilidade Auditiva (tapa ouvidos)", "Busca sensorial (toca em tudo)", 
                 "Agitação motora / Não para sentado", "Dificuldade na coordenação motora fina (lápis)",
                 "Baixa visão ou audição", "Seletividade alimentar (impacta lanche)"]
            )
            
        with st.expander("2. Cognitivo e Acadêmico (Processamento)"):
            st.session_state.dados['b_cognitiva'] = st.multiselect(
                "Desafios observados:",
                ["Tempo de atenção curto", "Dificuldade de abstração/metáforas", 
                 "Não realiza cópia do quadro", "Dificuldade na alfabetização/leitura",
                 "Dificuldade em organização/função executiva", "Rigidez cognitiva (não aceita erros)"]
            )
            
        with st.expander("3. Social e Comunicacional (Interação)"):
            st.session_state.dados['b_social'] = st.multiselect(
                "Desafios observados:",
                ["Não mantém contato visual", "Isolamento no recreio", 
                 "Comportamento opositor/desafiador", "Dificuldade em entender regras sociais",
                 "Comunicação não-verbal / Pouca fala", "Ecolalia (repete o que ouve)"]
            )

# === ABA 3: ESTRATÉGIAS E METAS ===
with tab3:
    st.subheader("🛠️ Plano de Intervenção")
    st.write("O sistema sugere estratégias baseadas nas barreiras selecionadas na aba anterior.")

    # LÓGICA INTELIGENTE DE SUGESTÃO
    sugestoes_acesso = []
    sugestoes_curriculo = []

    # Barreiras Sensoriais -> Acesso
    if "Hipersensibilidade Auditiva (tapa ouvidos)" in st.session_state.dados['b_sensorial']:
        sugestoes_acesso.append("Permitir uso de fones abafadores em momentos de ruído.")
        sugestoes_acesso.append("Antecipar verbalmente sinais sonoros (sinal do recreio).")
    if "Agitação motora / Não para sentado" in st.session_state.dados['b_sensorial']:
        sugestoes_acesso.append("Pausas ativas: permitir saídas rápidas para regulação.")
        sugestoes_acesso.append("Oferecer assento dinâmico ou permissão para ficar de pé.")

    # Barreiras Cognitivas -> Currículo e Acesso
    if "Não realiza cópia do quadro" in st.session_state.dados['b_cognitiva']:
        sugestoes_acesso.append("Fornecer pauta impressa do conteúdo (evitar cópia longa).")
        sugestoes_acesso.append("Permitir foto da lousa ou uso de escriba.")
    if "Tempo de atenção curto" in st.session_state.dados['b_cognitiva']:
        sugestoes_curriculo.append("Fragmentar atividades longas em etapas curtas (Passo a passo).")
        sugestoes_curriculo.append("Utilizar checklists visuais de conclusão de tarefa.")

    # Barreiras Sociais
    if "Comportamento opositor/desafiador" in st.session_state.dados['b_social']:
        sugestoes_acesso.append("Reforço positivo imediato para comportamentos adequados.")
        sugestoes_curriculo.append("Adaptação de provas: ambiente separado se necessário.")

    # Interface de Seleção
    col_est1, col_est2 = st.columns(2)
    with col_est1:
        st.markdown("**Adaptações de Acesso** (Como o aluno acessa a aula)")
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Selecione as aplicáveis:", 
            options=sugestoes_acesso + ["Uso de Tablet/Tecnologia", "Mobiliário Adaptado", "Material Ampliado", "Ledor/Escriba"],
            default=sugestoes_acesso
        )
        st.text_area("Outras adaptações de acesso:", key="outras_acesso")

    with col_est2:
        st.markdown("**Adaptações Curriculares** (Mudanças no conteúdo/avaliação)")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect(
            "Selecione as aplicáveis:", 
            options=sugestoes_curriculo + ["Redução do número de questões", "Conteúdo Prioritário (Foco no essencial)", "Avaliação Oral", "Tempo estendido (50% a mais)"],
            default=sugestoes_curriculo
        )
        st.text_area("Outras adaptações curriculares:", key="outras_curriculo")

# === ABA 4: GERAR DOCUMENTO ===
with tab4:
    st.subheader("🖨️ Finalização e Exportação")
    
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Preencha o Nome do Aluno na Aba 1 antes de gerar.")
    else:
        st.success("Tudo pronto! O sistema compilou os dados do Estudo de Caso e elaborou o PEI.")
        
        # Botão de Download
        doc_buffer = gerar_docx_completo(st.session_state.dados)
        
        col_d1, col_d2 = st.columns([2,1])
        with col_d1:
             st.markdown(f"""
             **Resumo do Documento:**
             * **Aluno:** {st.session_state.dados['nome']}
             * **Barreiras Mapeadas:** {len(st.session_state.dados['b_sensorial']) + len(st.session_state.dados['b_cognitiva'])}
             * **Estratégias Definidas:** {len(st.session_state.dados['estrategias_acesso']) + len(st.session_state.dados['estrategias_curriculo'])}
             """)
        with col_d2:
            st.download_button(
                label="📥 Baixar PEI em Word (.docx)",
                data=doc_buffer,
                file_name=f"PEI_{st.session_state.dados['nome'].replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.caption("Formato editável para ajustes finais da coordenação.")

    # Contexto Legal no Rodapé
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: grey; font-size: 0.8em;'>
    <b>Base Legal:</b> O Plano de Ensino Individualizado (PEI) é direito assegurado pelo Decreto nº 12.773/2025 
    e pela Lei Brasileira de Inclusão (Lei nº 13.146/2015).<br>
    Este documento substitui a necessidade de laudo médico para fins de adaptação escolar.
    </div>
    """, unsafe_allow_html=True)

