import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURAÇÃO VISUAL ARCO EDUCAÇÃO ---
st.set_page_config(
    page_title="PEI 360 | Arco Educação",
    page_icon="🧩",
    layout="wide"
)

# CSS para identidade visual (Azul Arco e Laranja)
st.markdown("""
    <style>
    /* Cores Arco Educação */
    :root {
        --arco-blue: #165DFF;
        --arco-orange: #FF7F00;
        --bg-gray: #F4F6F8;
    }
    .main {background-color: var(--bg-gray);}
    
    /* Cabeçalhos */
    h1, h2, h3 {color: #003366; font-family: 'Helvetica', sans-serif;}
    
    /* Botões personalizados */
    .stButton>button {
        background-color: #165DFF; 
        color: white; 
        border-radius: 8px;
        border: none;
        height: 3em;
        font-weight: bold;
    }
    .stButton>button:hover {background-color: #0044CC;}
    
    /* Box de Destaque */
    .highlight-box {
        padding: 1.5rem;
        background-color: white;
        border-left: 5px solid #FF7F00;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GERADORA DE WORD (.DOCX) ---
def gerar_docx(nome, serie, potencias, barreiras, estrategias, data_hoje):
    doc = Document()
    
    # Título
    titulo = doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtítulo com Lei
    sub = doc.add_paragraph(f'Base Legal: Decreto nº 12.773/2025 - PEI 360 Arco')
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Dados
    doc.add_heading('1. DADOS DE IDENTIFICAÇÃO', level=1)
    p = doc.add_paragraph()
    p.add_run('Nome do Estudante: ').bold = True
    p.add_run(nome)
    p.add_run('\nSérie/Ano: ').bold = True
    p.add_run(serie)
    p.add_run('\nData de Elaboração: ').bold = True
    p.add_run(data_hoje)

    # 2. Perfil
    doc.add_heading('2. ESTUDO DE CASO (SÍNTESE)', level=1)
    
    doc.add_heading('Potencialidades e Hiperfocos:', level=2)
    if potencias:
        for pot in potencias:
            doc.add_paragraph(pot, style='List Bullet')
    else:
        doc.add_paragraph('Não foram identificadas potencialidades nesta triagem.')

    doc.add_heading('Barreiras de Aprendizagem:', level=2)
    if barreiras:
        for bar in barreiras:
            doc.add_paragraph(bar, style='List Bullet')
    else:
        doc.add_paragraph('Nenhuma barreira específica reportada.')

    # 3. Plano
    doc.add_heading('3. PLANO DE AÇÃO PEDAGÓGICA', level=1)
    p = doc.add_paragraph('Estratégias para eliminação de barreiras (Art. 12 do Decreto 12.773):')
    if estrategias:
        for est in estrategias:
            doc.add_paragraph(est, style='List Bullet')
    else:
        doc.add_paragraph('Observação contínua necessária.')

    # 4. Assinaturas
    doc.add_paragraph('\n\n\n')
    doc.add_paragraph('_' * 40)
    doc.add_paragraph('Coordenação Pedagógica')
    
    # Salvar em memória
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- CABEÇALHO DO APP ---
col1, col2 = st.columns([1, 6])
with col1:
    st.markdown("## 🧩") # Aqui poderia ser o logo da Arco
with col2:
    st.title("PEI 360 | Solução de Inclusão")
    st.markdown("**Powered by Arco Educação** | _Compliance_ Decreto 12.773/25")

# --- NAVEGAÇÃO ---
tab_educ, tab_app, tab_legis = st.tabs(["📘 O que é o PEI?", "🚀 Gerador PEI 360", "⚖️ Legislação 2025"])

# --- ABA 1: EDUCATIVA ---
with tab_educ:
    st.markdown("""
    <div class="highlight-box">
    <h3>O que é o PEI?</h3>
    <p>O <b>Plano de Ensino Individualizado (PEI)</b> é o documento norteador da inclusão escolar. 
    Diferente de um laudo médico (que diz "o que o aluno tem"), o PEI diz <b>"como a escola deve agir"</b>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("**Para que serve?**\n\nPlanejar adaptações curriculares, definir metas pedagógicas e registrar a evolução do aluno, protegendo a escola juridicamente e garantindo o direito de aprender.")
    with col_b:
        st.warning("**Composição do Documento**\n\n1. **Histórico:** O que o aluno já sabe.\n2. **Estudo de Caso:** Barreiras e Potências.\n3. **Metas:** Onde queremos chegar.\n4. **Estratégias:** Como vamos chegar lá.")

# --- ABA 2: APLICAÇÃO (Gerador) ---
with tab_app:
    st.subheader("Mapeamento do Estudante")
    
    c1, c2 = st.columns(2)
    nome = c1.text_input("Nome do Estudante")
    serie = c2.selectbox("Série", ["Ed. Infantil", "Fund. I", "Fund. II", "Ensino Médio"])

    st.markdown("---")
    
    # Seleção Otimizada
    st.write("**1. Mapeamento de Potências (Alavancas de Aprendizagem)**")
    potencias_list = ["Memória Visual", "Interesse por Tecnologia", "Habilidade Artística", "Boa Oralidade", "Raciocínio Lógico"]
    potencias = st.multiselect("Selecione os pontos fortes:", potencias_list)

    st.write("**2. Mapeamento de Barreiras (Foco na eliminação)**")
    col_bar1, col_bar2 = st.columns(2)
    with col_bar1:
        barreiras_cog = st.multiselect("Barreiras Cognitivas/Atenção", ["Dificuldade de Foco", "Dificuldade de Abstração", "Lentidão na escrita"])
    with col_bar2:
        barreiras_soc = st.multiselect("Barreiras Sociais/Sensoriais", ["Hipersensibilidade Auditiva", "Dificuldade de Interação", "Comportamento Opositor"])
    
    barreiras = barreiras_cog + barreiras_soc

    # Botão de Ação
    if st.button("Gerar Documento PEI 360"):
        if not nome:
            st.error("Preencha o nome do aluno.")
        else:
            # Lógica simples de recomendação
            estrategias = []
            if "Dificuldade de Foco" in barreiras: estrategias.append("Fragmentar tarefas em etapas curtas.")
            if "Hipersensibilidade Auditiva" in barreiras: estrategias.append("Permitir uso de abafadores e antecipar ruídos.")
            if "Lentidão na escrita" in barreiras: estrategias.append("Oferecer tempo estendido ou ledor/escriba.")
            if not estrategias: estrategias.append("Aplicar Desenho Universal para Aprendizagem (DUA).")

            # Gerar DOCX
            arquivo_doc = gerar_docx(nome, serie, potencias, barreiras, estrategias, date.today().strftime('%d/%m/%Y'))
            
            st.success("Documento gerado com sucesso!")
            st.download_button(
                label="📥 Baixar PEI em Word (.docx)",
                data=arquivo_doc,
                file_name=f"PEI_360_{nome}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

# --- ABA 3: LEGISLAÇÃO ---
with tab_legis:
    st.markdown("""
    ### 🏛️ Contexto Legal: Decreto nº 12.773 (Dez/2025)
    
    Este decreto alterou significativamente a Política Nacional de Educação Especial.
    
    **Principais Mudanças para as Escolas:**
    * **Art. 12:** Torna obrigatória a realização de documento individualizado de natureza pedagógica (PEI/PAEE).
    * **Independência do Laudo:** O § 2º reforça que o suporte escolar **independe** de laudo médico, devendo basear-se no Estudo de Caso pedagógico.
    * **Financiamento:** O Art. 19-A assegura recursos do FUNDEB para ações de inclusão nas instituições parceiras.
    
    > *O PEI 360 foi desenhado para garantir que sua escola esteja 100% em conformidade com o Artigo 12 deste novo decreto.*
    """)

