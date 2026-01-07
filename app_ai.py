import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI
from pypdf import PdfReader
from fpdf import FPDF
import re
import base64
import os

# --- CONFIGURAÇÃO DA PÁGINA (WIDE & RESPONSIVA) ---
st.set_page_config(
    page_title="PEI 360º | Sistema Inclusivo",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL RESPONSIVO (MOBILE READY) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* FONTE & CORES GERAIS */
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    :root { 
        --brand-primary: #004E92; 
        --brand-secondary: #00796B;
        --bg-light: #F7FAFC; 
    }
    
    /* INPUTS AMIGÁVEIS */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important; border: 1px solid #CBD5E0 !important;
        padding: 10px;
    }

    /* CARDS DA HOME (GLASSMORPHISM) */
    .home-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        border-left: 6px solid var(--brand-primary);
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        height: 100%;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .home-card:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.08); border-color: var(--brand-primary); }
    
    .home-card h4 { 
        color: var(--brand-primary); 
        font-weight: 800; 
        font-size: 1.15rem; 
        margin-bottom: 12px; 
        display: flex; align-items: center; gap: 10px;
    }
    
    .home-card p { 
        font-size: 0.95rem; 
        color: #4A5568; 
        line-height: 1.6; 
        margin: 0; 
    }

    /* HEADER GRADIENTE (CSS PURO) */
    .header-container {
        padding: 20px;
        background: linear-gradient(135deg, #FFFFFF 0%, #E3F2FD 100%);
        border-radius: 16px;
        border-left: 8px solid var(--brand-primary);
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        flex-wrap: wrap; /* Permite quebrar linha no celular */
        gap: 20px;
    }

    /* BOTÕES CUSTOMIZADOS */
    .stButton>button {
        border-radius: 12px; font-weight: 700; height: 3.5em; width: 100%; 
        transition: 0.3s; border: none;
    }
    /* Botão Primário (PDF) */
    div[data-testid="column"] .stButton button[kind="primary"] {
        background-color: var(--brand-primary); color: white;
        box-shadow: 0 4px 6px rgba(0, 78, 146, 0.3);
    }
    /* Botão Secundário (Word) */
    div[data-testid="column"] .stButton button[kind="secondary"] {
        background-color: white; color: var(--brand-primary); 
        border: 2px solid var(--brand-primary);
    }
    .stButton>button:hover { transform: scale(1.02); }

    /* AJUSTES MOBILE */
    @media (max-width: 640px) {
        .header-container { flex-direction: column; text-align: center; }
        .header-text { border-left: none !important; padding-left: 0 !important; padding-top: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def encontrar_arquivo_logo():
    possiveis_nomes = ["360.png", "360.jpg", "logo.png", "logo.jpg"]
    for nome in possiveis_nomes:
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
    except Exception as e: return f"Erro: {e}"

def limpar_markdown(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    return texto

def limpar_para_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    texto = re.sub(r'[^\x00-\x7F\xA0-\xFF]', '', texto) 
    return texto

# --- INTELIGÊNCIA ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        serie = dados['serie'] if dados['serie'] else ""
        
        if "Infantil" in serie:
            foco_bncc = "Campos de Experiência e Objetivos de Aprendizagem"
        else:
            foco_bncc = "Habilidades Essenciais (Códigos Alfanuméricos)"

        prompt_sistema = f"""
        Você é um Coordenador Pedagógico Especialista em Inclusão.
        """
        
        contexto_extra = f"\n📄 LAUDO:{contexto_pdf[:3000]}" if contexto_pdf else ""
        nasc_str = str(dados.get('nasc', ''))
        
        prompt_usuario = f"""
        Estudante: {dados['nome']} | Série: {serie} | Idade: {nasc_str}
        Diag: {dados['diagnostico']} | Hiperfoco: {dados['hiperfoco']}
        {contexto_extra}
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        
        PARECER TÉCNICO (Estrutura):
        1. 🧠 Conexão Neural: Como usar o Hiperfoco.
        2. 🎯 Foco BNCC ({foco_bncc}): 1 objetivo da série adaptado.
        3. 💡 Ajuste Fino: Validação das estratégias escolhidas.
        """
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro DeepSeek: {str(e)}"

# --- PDF ---
class PDF(FPDF):
    def header(self):
        logo = encontrar_arquivo_logo()
        if logo:
            self.image(logo, x=10, y=8, w=25)
            x = 40
        else: x = 10
        self.set_font('Arial', 'B', 16); self.set_text_color(0, 78, 146)
        self.cell(x); self.cell(0, 10, 'PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'C'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Confidencial', 0, 0, 'C')

def gerar_pdf_nativo(dados):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
    def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("1. IDENTIFICAÇÃO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    nasc = dados.get('nasc'); d_nasc = nasc.strftime('%d/%m/%Y') if nasc else "-"
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nNascimento: {d_nasc}\nDiagnóstico: {dados['diagnostico']}"))
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("2. ESTRATÉGIAS EDUCACIONAIS"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    
    if dados['estrategias_acesso']:
        pdf.multi_cell(0, 7, txt("Acesso: " + limpar_para_pdf(', '.join(dados['estrategias_acesso']))))
    if dados['estrategias_ensino']:
        pdf.multi_cell(0, 7, txt("Metodologia: " + limpar_para_pdf(', '.join(dados['estrategias_ensino']))))
    if dados['estrategias_avaliacao']:
        pdf.multi_cell(0, 7, txt("Avaliação: " + limpar_para_pdf(', '.join(dados['estrategias_avaliacao']))))
    
    if dados['ia_sugestao']:
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("3. PARECER TÉCNICO"), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(limpar_para_pdf(dados['ia_sugestao'])))

    pdf.ln(15); pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.cell(0, 10, txt("Coordenação Pedagógica"), 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def gerar_docx_final(dados):
    doc = Document(); style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    doc.add_heading('PEI', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Nome: {dados['nome']}")
    if dados['ia_sugestao']:
        doc.add_heading('Parecer', level=1)
        doc.add_paragraph(limpar_markdown(dados['ia_sugestao']))
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- ESTADO INICIAL ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'escola': '', 'tem_laudo': False, 'diagnostico': '', 
        'rede_apoio': [], 'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'meta_acesso': '',
        'estrategias_ensino': [], 'meta_ensino': '',
        'estrategias_avaliacao': [], 'meta_avaliacao': '',
        'ia_sugestao': ''
    }
for k in ['estrategias_ensino', 'estrategias_avaliacao', 'meta_acesso', 'meta_ensino', 'meta_avaliacao', 'rede_apoio']:
    if k not in st.session_state.dados: st.session_state.dados[k] = [] if 'estrategias' in k or 'rede' in k else ''
if 'nasc' not in st.session_state.dados: st.session_state.dados['nasc'] = None
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# --- SIDEBAR ---
with st.sidebar:
    logo = encontrar_arquivo_logo()
    if logo: st.image(logo, width=120)
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']; st.success("✅ Chave Segura")
    else: api_key = st.text_input("Chave API:", type="password")
    st.markdown("---"); st.info("Versão 15.0 | Mobile Ready")

# --- CABEÇALHO RESPONSIVO ---
logo = encontrar_arquivo_logo()
header_html = ""
if logo:
    mime = "image/png" if logo.lower().endswith("png") else "image/jpeg"
    b64 = get_base64_image(logo)
    header_html = f"""
    <div class="header-container">
        <img src="data:{mime};base64,{b64}" style="max-height: 85px; width: auto; object-fit: contain;">
        <div class="header-text" style="border-left: 2px solid #CBD5E0; padding-left: 20px;">
            <p style="margin: 0; color: #4A5568; font-weight: 500; font-size: 1.1rem;">
                Planejamento Educacional Individualizado
            </p>
        </div>
    </div>
    """
else:
    header_html = '<div class="header-container"><i class="ri-global-line" style="font-size: 3.5rem; color: #004E92;"></i><div><h1 style="color: #004E92; margin: 0;">PEI 360º</h1></div></div>'

st.markdown(header_html, unsafe_allow_html=True)

# ABAS
abas = ["Início", "Estudante", "Mapeamento", "Plano de Ação", "Assistente de IA", "Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME (4 CARDS REORGANIZADOS)
with tab1:
    st.markdown("### <i class='ri-dashboard-line'></i> Ecossistema de Inclusão", unsafe_allow_html=True)
    st.write("")
    
    # CARD 1: DEFINIÇÃO
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-book-open-line"></i> 1. O que é o PEI?</h4>
            <p>O PEI não é burocracia, é <b>acessibilidade</b>. É o documento que oficializa como a escola vai flexibilizar o ensino para que o estudante aprenda do seu jeito, respeitando seu ritmo e potencial.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 2: LEGISLAÇÃO (OBRIGATORIEDADE)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-scales-3-line"></i> 2. Legislação (Res. Dez/2025)</h4>
            <p>Atenção: Conforme a LBI e Resoluções recentes, o PEI é <b>obrigatório</b> para qualquer estudante com barreira de aprendizagem, <b>independente de laudo médico</b>. A escola não pode esperar o diagnóstico para agir.</p>
        </div>
        """, unsafe_allow_html=True)

    # CARD 3: NEUROCIÊNCIA
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-brain-line"></i> 3. Neurociência</h4>
            <p>Focamos no <b>"Como Aprender"</b>. Se a memória de trabalho é curta, fragmentamos a tarefa. Se o controle inibitório é baixo, reduzimos distratores. É ciência aplicada à sala de aula.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 4: BNCC
    with c4:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-compass-3-line"></i> 4. Base Nacional (BNCC)</h4>
            <p>Não criamos um currículo paralelo. <b>Flexibilizamos</b> o currículo oficial. O estudante tem direito de acessar as mesmas Habilidades Essenciais da sua série, mas por caminhos diferentes.</p>
        </div>
        """, unsafe_allow_html=True)

# 2. ESTUDANTE
with tab2:
    st.info("Preencha os dados do estudante.")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    val_nasc = st.session_state.dados.get('nasc')
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", val_nasc, format="DD/MM/YYYY")
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione...")
    
    st.markdown("---")
    st.markdown("##### <i class='ri-history-line'></i> Contexto Escolar", unsafe_allow_html=True)
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Trajetória, retenções, escolas anteriores...")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="O que a família espera? Rotina em casa...")

    st.markdown("---")
    st.markdown("##### <i class='ri-stethoscope-line'></i> Saúde e Diagnóstico", unsafe_allow_html=True)
    c_diag, c_rede = st.columns(2)
    st.session_state.dados['diagnostico'] = c_diag.text_input("Diagnóstico (ou hipótese diagnóstica)", st.session_state.dados['diagnostico'])
    val_rede = st.session_state.dados.get('rede_apoio', [])
    st.session_state.dados['rede_apoio'] = c_rede.multiselect("Rede de Apoio:", ["Psicólogo", "Fonoaudiólogo", "Neuropediatra", "TO", "Psicopedagogo", "AT"], default=val_rede, placeholder="Selecione...")
    
    st.write("")
    with st.expander("📂 Anexar Laudo Médico (PDF)"):
        uploaded_file = st.file_uploader("Upload do arquivo", type="pdf", key="uploader_tab2")
        if uploaded_file is not None:
            texto = ler_pdf(uploaded_file)
            if texto: st.session_state.pdf_text = texto; st.success("✅ Laudo integrado à análise!")

# 3. MAPEAMENTO
with tab3:
    st.markdown("### <i class='ri-rocket-line'></i> Potencialidades", unsafe_allow_html=True)
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse intenso)")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes", "Oralidade", "Lógica"], placeholder="Selecione...")
    
    st.markdown("### <i class='ri-barricade-line'></i> Barreiras", unsafe_allow_html=True)
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade", "Busca Sensorial", "Seletividade", "Motora"], key="b_sens", placeholder="Selecione...")
    with st.expander("🧠 Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção Dispersa", "Memória Curta", "Rigidez Mental", "Lentidão Processamento", "Dificuldade Abstração"], key="b_cog", placeholder="Selecione...")
    with st.expander("❤️ Social"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Isolamento", "Baixa Tolerância Frustração", "Interpretação Literal", "Ansiedade Social"], key="b_soc", placeholder="Selecione...")

# 4. PLANO DE AÇÃO
with tab4:
    st.markdown("### <i class='ri-checkbox-circle-line'></i> Definição de Estratégias", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="home-card"><h4><i class="ri-layout-masonry-line"></i> 1. Acesso & Rotina</h4><p>Recursos para garantir que o aluno "esteja" na aula.</p></div>', unsafe_allow_html=True)
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido (+25%)", "Ledor/Escriba", "Material Ampliado", "Tablet", "Sala Silenciosa", "Pausas"], placeholder="Selecione...")

    with col_b:
        st.markdown('<div class="home-card"><h4><i class="ri-pencil-ruler-2-line"></i> 2. Metodologia</h4><p>Como o professor deve ensinar o conteúdo.</p></div>', unsafe_allow_html=True)
        st.session_state.dados['estrategias_ensino'] = st.multiselect("Estratégias:", ["Fragmentação", "Pistas Visuais", "Mapa Mental", "Redução de Volume", "Multisensorial"], placeholder="Selecione...")

    st.markdown("---")
    st.markdown('<div class="home-card"><h4><i class="ri-file-list-3-line"></i> 3. Avaliação</h4><p>Como o aluno pode demonstrar o que aprendeu.</p></div>', unsafe_allow_html=True)
    st.session_state.dados['estrategias_avaliacao'] = st.multiselect("Avaliação:", ["Prova Oral", "Sem Distratores", "Consulta Roteiro", "Trabalho/Projeto", "Enunciados Curtos"], placeholder="Selecione...")

# 5. ASSISTENTE DE IA
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### <i class='ri-robot-line'></i> Consultor Inteligente", unsafe_allow_html=True)
        st.info("Minha análise processa o histórico, laudo e barreiras para sugerir um plano pedagógico fundamentado.")
        
        status = "✅ Documento Anexado" if st.session_state.pdf_text else "⚪ Sem documento de apoio"
        st.markdown(f"**Status:** {status}")
        
        if st.button("✨ Gerar Parecer do Especialista", type="primary"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome do estudante.")
            else:
                with st.spinner("Analisando BNCC e Neurociência..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Análise Concluída!")
    
    with col_ia_right:
        st.markdown("### <i class='ri-file-text-line'></i> Parecer Técnico", unsafe_allow_html=True)
        if st.session_state.dados['ia_sugestao']:
            st.markdown(f"""
            <div style="background-color: white; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); line-height: 1.8;">
                {st.session_state.dados["ia_sugestao"].replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("O parecer técnico aparecerá aqui após o processamento.")

# 6. DOCUMENTO (BOTÕES EMPILHADOS À ESQUERDA)
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    
    if st.session_state.dados['nome']:
        # Layout: Botões na esquerda (coluna estreita), Espaço vazio na direita
        c_btn, c_info = st.columns([1, 3])
        
        with c_btn:
            docx = gerar_docx_final(st.session_state.dados)
            # Botão Secundário (Outline) - Word
            st.download_button(
                label="📥 Baixar em Word",
                data=docx,
                file_name=f"PEI_{st.session_state.dados['nome']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary"
            )
            
            st.write("") # Espaçamento visual
            
            pdf = gerar_pdf_nativo(st.session_state.dados)
            # Botão Primário (Sólido) - PDF
            st.download_button(
                label="📄 Baixar em PDF",
                data=pdf,
                file_name=f"PEI_{st.session_state.dados['nome']}.pdf",
                mime="application/pdf",
                type="primary"
            )
        
        with c_info:
            st.success("✅ Seu PEI está pronto!")
            st.markdown("Utilize o formato **Word** se precisar fazer edições manuais posteriores, ou **PDF** para arquivamento oficial seguro.")
            
    else:
        st.warning("Preencha o nome do estudante para liberar os downloads.")
    
    st.markdown("</div>", unsafe_allow_html=True)