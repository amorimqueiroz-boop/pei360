import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI
from pypdf import PdfReader
from fpdf import FPDF
import base64
import os
import re

# --- 1. CONFIGURAÇÃO E UTILITÁRIOS ---

def get_favicon():
    return "📘"

st.set_page_config(
    page_title="PEI 360º | Gestão Inclusiva",
    page_icon=get_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

def finding_logo():
    possiveis = ["360.png", "360.jpg", "logo.png", "logo.jpg", "iconeaba.png"]
    for nome in possiveis:
        if os.path.exists(nome): return nome
    return None

def get_base64_image(image_path):
    if not image_path: return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def ler_pdf(arquivo):
    if arquivo is None: return ""
    try:
        reader = PdfReader(arquivo)
        texto = ""
        for page in reader.pages: texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro na leitura do PDF: {e}"

def limpar_texto_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    texto = re.sub(r'[^\x00-\xff]', '', texto) 
    return texto

# --- 2. CSS AVANÇADO (DESIGN SYSTEM ARCO) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* RESET GLOBAL */
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    
    :root { 
        --brand-blue: #004E92; 
        --brand-coral: #FF6B6B; 
        --bg-light: #F7FAFC;
        --card-shadow: 0 4px 6px rgba(0,0,0,0.04);
        --border-radius-lg: 20px;
        --border-radius-sm: 12px;
    }

    /* REMOVER LINHA VERMELHA DAS ABAS (TAB HIGHLIGHT) */
    div[data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }

    /* ESTILO DAS ABAS (PÍLULAS) */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 25px;
        padding: 0 25px;
        background-color: white;
        border: 1px solid #E2E8F0;
        font-weight: 700;
        color: #718096;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-coral) !important;
        color: white !important;
        border-color: var(--brand-coral) !important;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    }

    /* CARD PADRÃO (USADO NO HEADER E NOS CONTEÚDOS) */
    .feature-card {
        background: white; 
        padding: 25px; 
        border-radius: var(--border-radius-lg);
        border: 1px solid #EDF2F7; 
        box-shadow: var(--card-shadow);
        height: 100%; 
        transition: all 0.3s ease;
        display: flex; flex-direction: column; align-items: flex-start;
    }
    .feature-card:hover { 
        transform: translateY(-2px); 
        border-color: var(--brand-blue); 
        box-shadow: 0 10px 15px rgba(0,0,0,0.05);
    }
    
    /* CABEÇALHO UNIFICADO */
    .header-container {
        background: white;
        padding: 25px;
        border-radius: var(--border-radius-lg);
        border: 1px solid #EDF2F7;
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
        display: flex; align-items: center; gap: 25px;
        /* Detalhe lateral azul para identidade */
        border-left: 6px solid var(--brand-blue); 
    }

    /* ÍCONES FLAT */
    .icon-box {
        width: 48px; height: 48px; 
        background: #EBF8FF; 
        border-radius: var(--border-radius-sm);
        display: flex; align-items: center; justify-content: center; 
        margin-bottom: 15px; flex-shrink: 0;
    }
    .icon-box i { font-size: 24px; color: var(--brand-blue); }

    /* TIPOGRAFIA CARDS */
    .feature-card h4 { color: var(--brand-blue); font-weight: 800; font-size: 1.1rem; margin-bottom: 8px; }
    .feature-card p { font-size: 0.95rem; color: #718096; line-height: 1.5; margin: 0; }

    /* INPUTS & BOTÕES */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] {
        border-radius: var(--border-radius-sm) !important;
        border-color: #CBD5E0 !important;
    }
    div[data-testid="column"] .stButton button {
        border-radius: var(--border-radius-sm) !important;
        font-weight: 700 !important;
        height: 3.5em !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. IA (LÓGICA UNIFICADA E ROBUSTA) ---
def consultar_ia_unificada(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ Configure a Chave API na barra lateral."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # Identificação de Altas Habilidades para ajuste de tom
        termo_ahsd = "Altas Habilidades/Superdotação" if "altas habilidades" in dados['diagnostico'].lower() or "superdotação" in dados['diagnostico'].lower() else dados['diagnostico']
        estrategia_macro = "Enriquecimento e Aprofundamento" if "altas habilidades" in dados['diagnostico'].lower() else "Flexibilização Curricular e Suporte"

        prompt_sistema = f"""
        Você é o Consultor Pedagógico Sênior do sistema PEI 360.
        Sua função é gerar o texto integral do Plano de Ensino Individualizado.
        Tom: Técnico, institucional, empático e resolutivo.
        Foco Central: {estrategia_macro}.
        """

        prompt_usuario = f"""
        DADOS DO ESTUDANTE:
        Nome: {dados['nome']} | Série: {dados['serie']} | Diagnóstico: {termo_ahsd}
        Hiperfoco: {dados['hiperfoco']}
        
        CONTEXTO (INTEGRAR AO TEXTO):
        Histórico: {dados['historico']}
        Família: {dados['familia']}
        
        REDE DE APOIO (CRUCIAL):
        Profissionais externos: {', '.join(dados['rede_apoio'])}
        Orientações recebidas (Clínica -> Escola): {dados['orientacoes_especialistas']}
        
        MAPEAMENTO DE BARREIRAS & SUPORTE:
        - Sensorial: {', '.join(dados['b_sensorial'])} (Nível: {dados['sup_sensorial']})
        - Cognitivo: {', '.join(dados['b_cognitiva'])} (Nível: {dados['sup_cognitiva']})
        - Social: {', '.join(dados['b_social'])} (Nível: {dados['sup_social']})
        
        ESTRATÉGIAS SELECIONADAS PELA ESCOLA:
        Acesso: {', '.join(dados['estrategias_acesso'])}
        Metodologia: {', '.join(dados['estrategias_ensino'])}
        Avaliação: {', '.join(dados['estrategias_avaliacao'])}
        
        LAUDO MÉDICO (EXTRA): {contexto_pdf[:1500]}
        
        GERE UM RELATÓRIO COMPLETO E ESTRUTURADO (SEM LISTAS EXCESSIVAS):
        1. ANÁLISE DO PERFIL (Sintetize histórico, diagnóstico e o impacto das barreiras).
        2. ESTRATÉGIAS DE INTERVENÇÃO (Como a escola aplicará as estratégias selecionadas e as orientações da rede de apoio no dia a dia).
        3. ADAPTAÇÃO CURRICULAR E AVALIAÇÃO (Como garantir o aprendizado conforme a BNCC e {estrategia_macro}).
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro DeepSeek: {str(e)}"

# --- 4. PDF PROFISSIONAL (COM BORDAS E FORMATAÇÃO) ---
class ProfessionalPDF(FPDF):
    def header(self):
        # Borda da página (Moldura)
        self.set_draw_color(0, 78, 146) # Azul Institucional
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)
        
        logo = finding_logo()
        if logo: 
            self.image(logo, 12, 12, 22)
            x_offset = 40
        else: x_offset = 12
        
        self.set_xy(x_offset, 15)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 8, 'PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'L')
        
        self.set_xy(x_offset, 22)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100)
        self.cell(0, 5, 'Documento Oficial | Sistema PEI 360º', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Uso Exclusivo da Equipe Pedagógica', 0, 0, 'C')

    def section_title(self, label):
        self.ln(5)
        self.set_fill_color(240, 248, 255) # Fundo azul suave
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(3)

def gerar_pdf_final(dados):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # 1. Identificação
    pdf.section_title("1. IDENTIFICAÇÃO E CONTEXTO")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    
    nasc_fmt = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "-"
    texto_ident = (
        f"Nome: {dados['nome']}\n"
        f"Data de Nascimento: {nasc_fmt}\n"
        f"Série/Ano: {dados['serie']}\n"
        f"Diagnóstico Clínico: {dados['diagnostico']}"
    )
    pdf.multi_cell(0, 6, limpar_texto_pdf(texto_ident))
    
    # 2. Rede de Apoio
    if dados['rede_apoio']:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Acompanhamento Multidisciplinar:", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, limpar_texto_pdf(', '.join(dados['rede_apoio'])))

    # 3. Corpo do Relatório (IA)
    if dados['ia_sugestao']:
        pdf.ln(4)
        # O título geralmente já vem na estrutura da IA, mas podemos reforçar
        # pdf.section_title("2. PARECER TÉCNICO E PLANO DE AÇÃO")
        texto_ia = limpar_texto_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, texto_ia)
        
    # 4. Assinaturas
    pdf.ln(20)
    y = pdf.get_y()
    if y > 250: pdf.add_page(); y = 40
    
    pdf.line(20, y, 90, y)
    pdf.line(120, y, 190, y)
    pdf.set_font("Arial", 'I', 8)
    pdf.text(30, y+5, "Coordenação Pedagógica")
    pdf.text(130, y+5, "Responsável Legal / Família")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    
    doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO', 0)
    doc.add_paragraph(f"Aluno(a): {dados['nome']}")
    doc.add_paragraph(f"Série: {dados['serie']} | Diagnóstico: {dados['diagnostico']}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Planejamento Pedagógico', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
        
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- 5. INTERFACE (ESTADO E SIDEBAR) ---

if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [],
        'rede_apoio': [], 'orientacoes_especialistas': '',
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_ensino': [], 'estrategias_avaliacao': [],
        'ia_sugestao': ''
    }
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# Sidebar
with st.sidebar:
    logo = finding_logo()
    if logo: st.image(logo, width=120)
    
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Sistema Ativo")
    else:
        api_key = st.text_input("Chave de Acesso (API):", type="password")
        
    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem; color:#718096;'>PEI 360º v2.21<br>Design System Integrado</div>", unsafe_allow_html=True)

# --- 6. LAYOUT PRINCIPAL ---

# Cabeçalho Visual (Agora com classe unificada)
logo_path = finding_logo()
b64_logo = get_base64_image(logo_path)
mime = "image/png" if logo_path and logo_path.endswith("png") else "image/jpeg"
img_html = f'<img src="data:{mime};base64,{b64_logo}" style="max-height: 80px; width: auto;">' if logo_path else ""

st.markdown(f"""
    <div class="header-container">
        {img_html}
        <div class="header-text" style="padding-left: 10px;">
            <p style="margin: 0; color: #004E92; font-weight: 800; font-size: 1.5rem; letter-spacing: -0.5px;">PEI 360º</p>
            <p style="margin: 0; color: #718096; font-size: 1rem;">Ecossistema de Gestão da Educação Inclusiva</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Abas de Navegação
abas = ["Início", "Estudante", "Rede de Apoio", "Mapeamento", "Plano de Ação", "Assistente IA", "Documento"]
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# TAB 0: Início (Cards Informativos)
with tab0:
    st.markdown("### <i class='ri-dashboard-line'></i> Visão Geral", unsafe_allow_html=True)
    st.write("")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-book-open-line"></i></div>
            <h4>O que é o PEI?</h4>
            <p>O PEI (Plano de Ensino Individualizado) é o documento oficial que garante a acessibilidade curricular. Ele não reduz o conteúdo, mas adapta o <b>meio</b> de acesso.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-scales-3-line"></i></div>
            <h4>Legislação & Direito</h4>
            <p>Em conformidade com a LBI e o Decreto 12.686/2025. O PEI é direito do estudante com barreiras de aprendizagem, independente de laudo fechado.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-brain-line"></i></div>
            <h4>Neurociência na Prática</h4>
            <p>Foco nas Funções Executivas: utilizamos as potencialidades (hiperfoco) para mitigar as barreiras cognitivas e sensoriais.</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-compass-3-line"></i></div>
            <h4>BNCC & Equidade</h4>
            <p>Garantimos os Direitos de Aprendizagem e as Competências Gerais, flexibilizando as habilidades conforme a necessidade específica.</p>
        </div>
        """, unsafe_allow_html=True)

# TAB 1: Estudante
with tab1:
    st.markdown("### <i class='ri-user-smile-line'></i> Dossiê do Estudante", unsafe_allow_html=True)
    st.info("Preencha os dados essenciais para identificação e contexto inicial.")
    
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Ano/Série", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "Fund. II (6º-9º)", "Ensino Médio"], placeholder="Selecione...")
    
    st.write("")
    st.session_state.dados['diagnostico'] = st.text_input(
        "Diagnóstico Clínico (ou Hipótese)", 
        st.session_state.dados['diagnostico'],
        help="Ex: TEA, TDAH. Se for Altas Habilidades, especifique para ativar o enriquecimento curricular."
    )

    st.markdown("---")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar (Resumo da trajetória)", height=100)
    st.session_state.dados['familia'] = cf.text_area("Contexto Familiar e Expectativas", height=100)
    
    with st.expander("📎 Upload de Laudo Médico (PDF)"):
        up = st.file_uploader("Selecione o arquivo", type="pdf")
        if up:
            st.session_state.pdf_text = ler_pdf(up)
            st.success("Documento analisado com sucesso!")

# TAB 2: Rede de Apoio
with tab2:
    st.markdown("### <i class='ri-team-line'></i> Rede de Apoio Externa", unsafe_allow_html=True)
    st.info("Registre as orientações dos terapeutas para alinhar a conduta escolar.")
    
    c_rede1, c_rede2 = st.columns(2)
    st.session_state.dados['rede_apoio'] = c_rede1.multiselect(
        "Profissionais que atendem o aluno:", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psicopedagogo", "Professor Particular"],
        placeholder="Selecione..."
    )
    
    st.session_state.dados['orientacoes_especialistas'] = st.text_area(
        "Orientações Técnicas (O que a escola deve fazer?)",
        placeholder="Ex: A Fonoaudióloga solicitou uso de pistas visuais na lousa e tempo maior para processamento oral.",
        height=150
    )

# TAB 3: Mapeamento
with tab3:
    st.markdown("### <i class='ri-map-pin-user-line'></i> Mapeamento de Perfil", unsafe_allow_html=True)
    st.info("Identifique barreiras e defina o nível de suporte necessário.")
    
    st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Áreas de Interesse (Alavanca de engajamento)")
    
    # Sensorial
    with st.expander("Perfil Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade Auditiva", "Hipersensibilidade Visual", "Busca Sensorial", "Baixo Tônus", "Agitação Motora"], placeholder="Selecione...")
        st.write("Nível de Suporte:")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte Sensorial", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_sens")

    # Cognitivo
    with st.expander("Perfil Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção Sustentada", "Memória de Trabalho", "Rigidez Cognitiva", "Velocidade de Processamento", "Abstração"], placeholder="Selecione...")
        st.write("Nível de Suporte:")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte Cognitivo", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_cog")

    # Social
    with st.expander("Perfil Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Interação com Pares", "Tolerância à Frustração", "Compreensão de Regras", "Isolamento"], placeholder="Selecione...")
        st.write("Nível de Suporte:")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte Social", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_soc")

# TAB 4: Plano de Ação
with tab4:
    st.markdown("### <i class='ri-tools-line'></i> Definição de Estratégias", unsafe_allow_html=True)
    st.info("Selecione os recursos que serão mobilizados para eliminar as barreiras mapeadas.")
    
    c_acesso, c_ensino = st.columns(2)
    with c_acesso:
        st.markdown("#### Acesso ao Currículo")
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Recursos de Acessibilidade:", 
            ["Tempo Estendido (+25%)", "Apoio à Leitura e Escrita (Ledor/Escriba)", "Material Ampliado", "Sala com Redução de Estímulos", "Uso de Tecnologia Assistiva", "Pausas Programadas"],
            placeholder="Selecione..."
        )
        
    with c_ensino:
        st.markdown("#### Metodologia de Ensino")
        st.session_state.dados['estrategias_ensino'] = st.multiselect(
            "Estratégias Didáticas:", 
            ["Fragmentação de Tarefas", "Pistas Visuais e Mapas Mentais", "Enriquecimento Curricular (AH/SD)", "Antecipação de Rotina", "Aprendizagem Baseada em Projetos"],
            placeholder="Selecione..."
        )
    
    st.write("")
    st.markdown("#### Avaliação Diferenciada")
    st.session_state.dados['estrategias_avaliacao'] = st.multiselect(
        "Como avaliar?", 
        ["Prova Adaptada (Conteúdo)", "Prova com Consulta", "Avaliação Oral", "Trabalhos e Projetos", "Sem Distratores Visuais"],
        placeholder="Selecione..."
    )

# TAB 5: Assistente IA
with tab5:
    st.markdown("### <i class='ri-robot-line'></i> Consultor Inteligente", unsafe_allow_html=True)
    st.info("O Assistente analisará todos os dados (Histórico, Laudo, Rede de Apoio e Barreiras) para redigir o PEI completo.")
    
    col_btn, col_res = st.columns([1, 3])
    with col_btn:
        st.write("")
        st.write("")
        if st.button("GERAR PEI AGORA", type="primary"):
            if not st.session_state.dados['nome']:
                st.error("Por favor, preencha o nome do estudante.")
            else:
                with st.spinner("Processando dados e redigindo documento..."):
                    res, err = consultar_ia_unificada(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Documento gerado!")
    
    with col_res:
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Texto do Relatório (Editável):", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.markdown("""
            <div style='padding:50px; text-align:center; color:#A0AEC0; border:2px dashed #CBD5E0; border-radius:12px; background-color: #F7FAFC;'>
                <i class="ri-file-text-line" style="font-size: 30px;"></i><br><br>
                O parecer técnico detalhado aparecerá aqui após a geração.
            </div>
            """, unsafe_allow_html=True)

# TAB 6: Documento
with tab6:
    st.markdown("### <i class='ri-file-pdf-line'></i> Exportação Oficial", unsafe_allow_html=True)
    
    if st.session_state.dados['ia_sugestao']:
        c_pdf, c_word = st.columns(2)
        with c_pdf:
            st.markdown("#### Arquivo PDF (Final)")
            st.caption("Documento formatado com bordas institucionais, pronto para assinatura.")
            pdf_bytes = gerar_pdf_final(st.session_state.dados)
            st.download_button("📥 Baixar PDF", pdf_bytes, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            
        with c_word:
            st.markdown("#### Arquivo Word (Editável)")
            st.caption("Para ajustes finos na formatação ou conteúdo.")
            docx_bytes = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar Word", docx_bytes, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("⚠️ Gere o conteúdo na aba 'Assistente IA' antes de exportar o documento.")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8rem;'>PEI 360º v2.21 | Desenvolvido por Rodrigo Queiroz</div>", unsafe_allow_html=True)