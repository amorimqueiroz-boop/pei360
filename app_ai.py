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

# --- 1. CONFIGURAÇÃO INICIAL E UTILITÁRIOS ---

def get_favicon():
    return "📘"

st.set_page_config(
    page_title="PEI 360º | Inclusão & Alta Performance",
    page_icon=get_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

def finding_logo():
    # Tenta encontrar logo no diretório
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
    except Exception as e: return f"Erro ao ler PDF: {e}"

def limpar_texto_pdf(texto):
    if not texto: return ""
    # Substitui formatações de markdown por texto limpo
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    # Remove caracteres incompatíveis com Latin-1 (padrão FPDF)
    texto = re.sub(r'[^\x00-\xff]', '', texto) 
    return texto

# --- 2. CSS PROFISSIONAL (CORRIGIDO) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* Global */
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    
    :root { 
        --brand-blue: #004E92; 
        --brand-coral: #FF6B6B; 
        --bg-light: #F7FAFC;
    }

    /* Header Unificado e Limpo */
    .header-box {
        background: white;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #EDF2F7;
        border-top: 6px solid var(--brand-blue);
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    /* Cards de Funcionalidade */
    .feature-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 100%;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        border-color: var(--brand-blue);
    }
    
    /* Ícones */
    .icon-box {
        width: 40px; height: 40px;
        background: #EBF8FF;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 15px;
    }
    .icon-box i { font-size: 20px; color: var(--brand-blue); }

    /* Inputs e Botões */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px;
        padding: 0 20px;
        background-color: white;
        border: 1px solid #E2E8F0;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-coral) !important;
        color: white !important;
        border-color: var(--brand-coral) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE IA (RELATÓRIO UNIFICADO) ---
def consultar_ia_v219(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ Insira a chave da API na barra lateral."
    
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # Identificação de Altas Habilidades
        is_ahsd = "altas habilidades" in dados['diagnostico'].lower() or "superdotação" in dados['diagnostico'].lower()
        termo_chave = "ENRIQUECIMENTO CURRICULAR" if is_ahsd else "FLEXIBILIZAÇÃO CURRICULAR"
        
        prompt_sistema = f"""
        Você é um Especialista em Educação Inclusiva e Neurociência.
        Sua missão é redigir o PARECER TÉCNICO COMPLETO do PEI (Plano de Ensino Individualizado).
        
        DIRETRIZES:
        1. Gere um texto corrido, profissional e empático. Não use tópicos soltos.
        2. O texto deve cruzar: Histórico do aluno + Diagnóstico + Orientações da Rede de Apoio + BNCC.
        3. FOCO: {termo_chave}. Se for Altas Habilidades, sugira aprofundamento e desafios. Se for dificuldade, sugira suporte.
        4. O texto será colado diretamente no PDF oficial. Capriche na linguagem formal pedagógica.
        """

        prompt_usuario = f"""
        DADOS DO ESTUDANTE:
        Nome: {dados['nome']} | Série: {dados['serie']} | Diagnóstico: {dados['diagnostico']}
        Hiperfoco/Interesses: {dados['hiperfoco']}
        
        CONTEXTO:
        Histórico Escolar: {dados['historico']}
        Família: {dados['familia']}
        
        REDE DE APOIO (IMPORTANTE):
        Profissionais que atendem: {', '.join(dados['rede_apoio'])}
        Orientações Clínicas recebidas: {dados['orientacoes_especialistas']}
        (Incorpore essas orientações clínicas nas estratégias de sala de aula).
        
        MAPEAMENTO:
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        Estratégias sugeridas pela escola: {', '.join(dados['estrategias_acesso'] + dados['estrategias_ensino'])}
        
        LAUDO MÉDICO (Resumo): {contexto_pdf[:2000]}
        
        GERE O PARECER EM 3 SEÇÕES CLARAS (Use títulos em Maiúsculas):
        1. ANÁLISE DO PERFIL BIOPSICOSSOCIAL
        2. PLANO DE INTERVENÇÃO PEDAGÓGICA E {termo_chave}
        3. CONCLUSÃO E ORIENTAÇÕES PARA AVALIAÇÃO
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro na IA: {str(e)}"

# --- 4. PDF PROFISSIONAL COM BORDAS ---
class ProfessionalPDF(FPDF):
    def header(self):
        # Borda da Página (Moldura)
        self.set_line_width(0.5)
        self.set_draw_color(0, 78, 146) # Azul borda
        self.rect(5, 5, 200, 287)
        
        # Logo e Título
        logo = finding_logo()
        if logo: 
            self.image(logo, 12, 12, 25)
            offset_x = 40
        else: 
            offset_x = 12
            
        self.set_xy(offset_x, 15)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 10, 'PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0, 1, 'L')
        
        self.set_xy(offset_x, 22)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100)
        self.cell(0, 5, 'Documento Oficial de Planejamento Pedagógico', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Sistema PEI 360 | Página {self.page_no()}', 0, 0, 'C')

    def section_title(self, label):
        self.set_fill_color(240, 245, 255) # Azul bem claro
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.ln(5)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(2)

def gerar_pdf_v219(dados):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # 1. Dados Cadastrais (Fixo)
    pdf.section_title("1. IDENTIFICAÇÃO DO ESTUDANTE")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    
    nasc = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "Não informado"
    pdf.multi_cell(0, 6, limpar_texto_pdf(f"Nome: {dados['nome']}\nData de Nascimento: {nasc}\nSérie Atual: {dados['serie']}\nDiagnóstico: {dados['diagnostico']}"))
    
    # 2. Rede de Apoio (Novo)
    if dados['rede_apoio']:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Rede de Apoio Externa:", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, limpar_texto_pdf(', '.join(dados['rede_apoio'])))
    
    # 3. Relatório da IA (Corpo Principal)
    if dados['ia_sugestao']:
        pdf.ln(5)
        # O título da seção já vem no texto da IA ou podemos forçar aqui
        # pdf.section_title("2. PARECER TÉCNICO E PLANEJAMENTO")
        texto_ia = limpar_texto_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, texto_ia)
        
    # 4. Assinaturas
    pdf.ln(25)
    y = pdf.get_y()
    
    # Verifica se cabe na página, senão cria nova
    if y > 250: 
        pdf.add_page()
        y = pdf.get_y() + 20
        
    pdf.line(20, y, 90, y)
    pdf.line(120, y, 190, y)
    pdf.set_font("Arial", 'I', 8)
    pdf.text(35, y+5, "Coordenação Pedagógica")
    pdf.text(135, y+5, "Responsável / Família")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_docx_v219(dados):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(11)
    
    doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO', 0)
    doc.add_paragraph(f"Estudante: {dados['nome']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Parecer Técnico', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
        
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 5. INTERFACE DO USUÁRIO (STREAMLIT) ---

# Estado da Sessão
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [],
        'rede_apoio': [], 'orientacoes_especialistas': '',
        'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
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
        st.success("✅ API Integrada")
    else:
        api_key = st.text_input("Insira sua API Key:", type="password")
        
    st.markdown("---")
    st.info("v2.19 | Atualização AH/SD & Rede de Apoio")

# Header Visual
logo_path = finding_logo()
img_tag = ""
if logo_path:
    b64 = get_base64_image(logo_path)
    img_tag = f'<img src="data:image/png;base64,{b64}" style="height: 60px;">'

st.markdown(f"""
    <div class="header-box">
        {img_tag}
        <div>
            <h2 style="margin:0; color: #004E92; font-weight: 800;">PEI 360º</h2>
            <p style="margin:0; color: #718096;">Sistema de Gestão da Aprendizagem Inclusiva</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Estudante", "2. Rede de Apoio", "3. Mapeamento", "4. Estratégias", "5. Inteligência Artificial", "6. Documento"
])

# TAB 1: Estudante
with tab1:
    st.markdown("### 👤 Identificação e Diagnóstico")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Data Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "Fund. I (1-5)", "Fund. II (6-9)", "Ensino Médio"])
    
    st.warning("⚠️ Atenção: Se o aluno tiver Altas Habilidades, digite 'Altas Habilidades' no diagnóstico abaixo.")
    st.session_state.dados['diagnostico'] = st.text_input("Diagnóstico Clínico (Ex: TEA, TDAH, Dislexia, Altas Habilidades/Superdotação)")
    
    st.markdown("---")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar (Retenções, mudanças de escola)", height=100)
    st.session_state.dados['familia'] = cf.text_area("Contexto Familiar (Expectativas, rotina)", height=100)
    
    with st.expander("Anexar Laudo PDF (Opcional)"):
        up = st.file_uploader("Upload PDF", type="pdf")
        if up: 
            st.session_state.pdf_text = ler_pdf(up)
            st.success("Laudo lido com sucesso!")

# TAB 2: Rede de Apoio (NOVA)
with tab2:
    st.markdown("### 🤝 Rede de Apoio Multidisciplinar")
    st.info("Aqui integramos as orientações dos terapeutas ao ambiente escolar.")
    
    c_rede1, c_rede2 = st.columns(2)
    st.session_state.dados['rede_apoio'] = c_rede1.multiselect(
        "Quem atende o estudante?", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Psicopedagogo", "Neuropediatra", "Professor Particular"]
    )
    
    st.session_state.dados['orientacoes_especialistas'] = st.text_area(
        "Orientações Técnicas (O que os especialistas pediram para a escola fazer?)",
        placeholder="Ex: A fonoaudióloga solicitou que o aluno sente na primeira fileira e use pistas visuais...",
        height=150
    )

# TAB 3: Mapeamento
with tab3:
    st.markdown("### 🧠 Perfil de Aprendizagem")
    st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Interesses (Essencial para engajamento)")
    
    c_bar1, c_bar2, c_bar3 = st.columns(3)
    with c_bar1:
        st.markdown("**Sensorial/Físico**")
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade Sonora", "Hipersensibilidade Visual", "Busca Sensorial", "Agitação Motora"], key="b1")
    with c_bar2:
        st.markdown("**Cognitivo**")
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção/Foco", "Memória de Trabalho", "Rigidez Cognitiva", "Velocidade de Processamento"], key="b2")
    with c_bar3:
        st.markdown("**Social/Emocional**")
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Interação com Pares", "Tolerância à Frustração", "Autorregulação", "Compreensão de Regras"], key="b3")

# TAB 4: Estratégias
with tab4:
    st.markdown("### 🛠️ Plano de Ação (Checklist)")
    c_est1, c_est2 = st.columns(2)
    with c_est1:
        st.markdown("#### Acesso ao Currículo")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Adaptações:", ["Tempo Estendido", "Material Ampliado", "Redutor de Ruído", "Ledor/Escriba", "Uso de Tablet", "Enriquecimento Curricular (AH/SD)"])
    with c_est2:
        st.markdown("#### Metodologia de Ensino")
        st.session_state.dados['estrategias_ensino'] = st.multiselect("Estratégias:", ["Pistas Visuais", "Fragmentação de Tarefas", "Aprendizagem Baseada em Projetos", "Gamificação", "Mapa Mental"])

# TAB 5: IA
with tab5:
    st.markdown("### 🤖 Redator Especialista")
    st.info("A IA irá gerar o relatório completo unificando os dados das abas anteriores.")
    
    col_btn, col_res = st.columns([1, 3])
    
    with col_btn:
        st.write("")
        st.write("")
        if st.button("GERAR RELATÓRIO COMPLETO", type="primary"):
            if not st.session_state.dados['nome']:
                st.error("Preencha o nome do aluno na Aba 1.")
            else:
                with st.spinner("O DeepSeek está analisando o caso e redigindo o PEI..."):
                    res, err = consultar_ia_v219(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Relatório Gerado!")
    
    with col_res:
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Prévia do Texto (Editável):", st.session_state.dados['ia_sugestao'], height=400)
        else:
            st.markdown("""
            <div style="text-align:center; color: #A0AEC0; padding: 40px; border: 2px dashed #CBD5E0; border-radius: 10px;">
                O texto do relatório aparecerá aqui.
            </div>
            """, unsafe_allow_html=True)

# TAB 6: Documento
with tab6:
    st.markdown("### 📄 Exportação Oficial")
    if st.session_state.dados['ia_sugestao']:
        c_pdf, c_word = st.columns(2)
        
        with c_pdf:
            st.markdown("#### Versão PDF (Final)")
            pdf_data = gerar_pdf_v219(st.session_state.dados)
            st.download_button("📥 Baixar PDF Institucional", pdf_data, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            st.caption("Documento com bordas, logo e diagramação oficial.")
            
        with c_word:
            st.markdown("#### Versão Word (Editável)")
            docx_data = gerar_docx_v219(st.session_state.dados)
            st.download_button("📥 Baixar DOCX", docx_data, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("Gere o relatório na aba 'Inteligência Artificial' antes de baixar.")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8rem;'>PEI 360º v2.19 | Desenvolvido por Rodrigo Queiroz</div>", unsafe_allow_html=True)
st.caption("PEI 360º v2.19 | Desenvolvido por Rodrigo Queiroz")