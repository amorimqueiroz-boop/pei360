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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Sistema Inclusivo",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL PREMIUM (ULTIMATE UI) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    :root { --brand-primary: #004E92; --brand-light: #E3F2FD; --text-dark: #1A202C; }
    
    /* ABAS ESTILIZADAS (TAB NAVIGATION) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #FFFFFF;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        color: #4A5568;
        padding: 0 20px;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-primary) !important;
        color: white !important;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 78, 146, 0.3);
    }

    /* CARDS DA HOME (GLASSMORPHISM) */
    .home-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        height: 100%;
        transition: transform 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .home-card:hover { transform: translateY(-5px); border-color: var(--brand-primary); }
    .home-card::before {
        content: ""; position: absolute; top: 0; left: 0; width: 6px; height: 100%;
        background: var(--brand-primary);
    }
    .home-card h4 { 
        color: var(--brand-primary); font-weight: 800; font-size: 1.2rem; 
        margin-bottom: 15px; display: flex; align-items: center; gap: 10px;
    }
    .home-card p { font-size: 0.95rem; color: #4A5568; line-height: 1.6; margin: 0; }
    
    /* INPUTS & UPLOAD */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px !important; border: 1px solid #CBD5E0 !important;
    }
    div[data-testid="stFileUploader"] section { 
        background-color: #F8FAFC; border: 2px dashed #A0AEC0; border-radius: 12px;
    }

    /* BOTÕES */
    .stButton>button {
        border-radius: 10px; font-weight: 700; height: 3.5em; width: 100%; transition: 0.3s;
    }
    /* Botão Primário (Solid) */
    div[data-testid="column"] .stButton button[kind="primary"] {
        background-color: #004E92; color: white; border: none;
    }
    /* Botão Secundário (Outline - Simulando com CSS padrão) */
    div[data-testid="column"] .stButton button[kind="secondary"] {
        background-color: white; color: #004E92; border: 2px solid #004E92;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
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
        Estratégias Escola: {', '.join(dados['estrategias_acesso'] + dados['estrategias_ensino'])}
        
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
    st.markdown("---"); st.info("Versão 14.0 | Ultimate")

# --- CABEÇALHO ---
logo = encontrar_arquivo_logo()
if logo:
    mime = "image/png" if logo.lower().endswith("png") else "image/jpeg"
    b64 = get_base64_image(logo)
    header_inner = f'<div style="display: flex; align-items: center; height: 100%;"><img src="data:{mime};base64,{b64}" style="max-height: 85px; width: auto; margin-right: 20px;"><div style="border-left: 2px solid #CBD5E0; padding-left: 20px; height: 60px; display: flex; align-items: center;"><p style="margin: 0; color: #4A5568; font-weight: 500; font-size: 1.1rem;">Planejamento Educacional Individualizado</p></div></div>'
else:
    header_inner = '<div style="display: flex; align-items: center;"><i class="ri-global-line" style="font-size: 3.5rem; margin-right: 20px; color: #004E92;"></i><div><h1 style="color: #004E92; margin: 0; font-weight: 800; font-size: 2.5rem; line-height: 1;">PEI 360º</h1><p style="margin: 5px 0 0 0; color: #4A5568;">Sistema de Inclusão</p></div></div>'

st.markdown(f"""
<div style="padding: 15px 25px; background: linear-gradient(90deg, #FFFFFF 0%, #E3F2FD 100%); border-radius: 15px; border-left: 8px solid #004E92; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; min-height: 100px; display: flex; align-items: center;">
    {header_inner}
</div>
""", unsafe_allow_html=True)

# ABAS COM VISUAL DE APP
abas = ["Início", "Estudante", "Mapeamento", "Plano de Ação", "Assistente de IA", "Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME (4 CARDS REORGANIZADOS)
with tab1:
    st.markdown("### <i class='ri-dashboard-line'></i> Ecossistema de Inclusão", unsafe_allow_html=True)
    st.write("")
    
    # CARD 1: O QUE É O PEI
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-book-open-line"></i> 1. O que é o PEI?</h4>
            <p>O <b>Plano de Ensino Individualizado</b> é o "mapa da mina" para a inclusão. Ele não é um facilitador, mas um <b>acessibilizador</b> do currículo, desenhando rotas personalizadas para que o estudante alcance seu máximo potencial.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 2: LEGISLAÇÃO (ATUALIZADO)
    with c2:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-scales-3-line"></i> 2. Legislação (Res. Dez/2025)</h4>
            <p>Atenção: A nova Resolução do Conselho Nacional reafirma que o PEI é <b>obrigatório</b> para estudantes com barreiras de aprendizagem, <b>independente de laudo médico fechado</b>. A escola deve iniciar as adaptações imediatamente.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    # CARD 3: NEUROCIÊNCIA
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-brain-line"></i> 3. Neurociência</h4>
            <p>Nossa inteligência foca nas <b>Funções Executivas</b> (memória operacional, controle inibitório, flexibilidade). Entendemos "como" o cérebro processa para sugerir "como" ensinar.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # CARD 4: BNCC
    with c4:
        st.markdown("""
        <div class="home-card">
            <h4><i class="ri-compass-3-line"></i> 4. Conexão BNCC</h4>
            <p>Não recortamos o currículo; flexibilizamos. Na Ed. Infantil focamos em <b>Campos de Experiência</b> e no Fundamental/Médio nas <b>Habilidades Essenciais</b> para garantir o direito de aprendizagem.</p>
        </div>
        """, unsafe_allow_html=True)

# 2. ESTUDANTE
with tab2:
    st.info("Dossiê do Estudante.")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    val_nasc = st.session_state.dados.get('nasc')
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", val_nasc, format="DD/MM/YYYY")
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione...")
    
    st.markdown("---")
    st.markdown("##### <i class='ri-history-line'></i> Histórico e Contexto", unsafe_allow_html=True)
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Escolas anteriores...")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="Expectativas e rotina...")

    st.markdown("---")
    st.markdown("##### <i class='ri-stethoscope-line'></i> Clínico e Apoio", unsafe_allow_html=True)
    c_diag, c_rede = st.columns(2)
    st.session_state.dados['diagnostico'] = c_diag.text_input("Diagnóstico (ou hipótese)", st.session_state.dados['diagnostico'])
    val_rede = st.session_state.dados.get('rede_apoio', [])
    st.session_state.dados['rede_apoio'] = c_rede.multiselect("Rede de Apoio:", ["Psicólogo", "Fonoaudiólogo", "Neuropediatra", "TO", "Psicopedagogo", "AT"], default=val_rede, placeholder="Selecione...")
    
    st.write("")
    with st.expander("📂 Anexar Laudo Médico (PDF) - Opcional"):
        uploaded_file = st.file_uploader("Arraste o arquivo aqui", type="pdf", key="uploader_tab2")
        if uploaded_file is not None:
            texto = ler_pdf(uploaded_file)
            if texto: st.session_state.pdf_text = texto; st.success("✅ Laudo integrado à análise!")

# 3. MAPEAMENTO
with tab3:
    st.markdown("### <i class='ri-rocket-line'></i> Potencialidades", unsafe_allow_html=True)
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes", "Oralidade", "Lógica"], placeholder="Selecione...")
    
    st.markdown("### <i class='ri-barricade-line'></i> Barreiras", unsafe_allow_html=True)
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade", "Busca Sensorial", "Seletividade", "Motora"], key="b_sens", placeholder="Selecione...")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_sens")
    with st.expander("🧠 Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção", "Memória", "Rigidez", "Lentidão", "Abstração"], key="b_cog", placeholder="Selecione...")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_cog")
    with st.expander("❤️ Social"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Isolamento", "Frustração", "Literalidade", "Ansiedade"], key="b_soc", placeholder="Selecione...")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_soc")

# 4. PLANO DE AÇÃO
with tab4:
    st.markdown("### <i class='ri-checkbox-circle-line'></i> Estratégias", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="action-card"><h4><i class="ri-layout-masonry-line"></i> 1. Acesso</h4><p>Organização e Tempo.</p></div>', unsafe_allow_html=True)
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido (+25%)", "Ledor/Escriba", "Material Ampliado", "Tablet", "Sala Silenciosa", "Pausas"], placeholder="Selecione...")
        st.session_state.dados['meta_acesso'] = st.text_input("Meta Acesso:", placeholder="Ex: Permanecer em sala...")

    with col_b:
        st.markdown('<div class="action-card"><h4><i class="ri-pencil-ruler-2-line"></i> 2. Metodologia</h4><p>Ensino e Conteúdo.</p></div>', unsafe_allow_html=True)
        st.session_state.dados['estrategias_ensino'] = st.multiselect("Estratégias:", ["Fragmentação", "Pistas Visuais", "Mapa Mental", "Redução de Volume", "Multisensorial"], placeholder="Selecione...")
        st.session_state.dados['meta_ensino'] = st.text_input("Meta Ensino:", placeholder="Ex: Realizar atividade com autonomia...")

    st.markdown("---")
    st.markdown('<div class="action-card"><h4><i class="ri-file-list-3-line"></i> 3. Avaliação Diferenciada</h4><p>Demonstração do saber.</p></div>', unsafe_allow_html=True)
    st.session_state.dados['estrategias_avaliacao'] = st.multiselect("Avaliação:", ["Prova Oral", "Sem Distratores", "Consulta Roteiro", "Trabalho/Projeto", "Enunciados Curtos"], placeholder="Selecione...")
    st.session_state.dados['meta_avaliacao'] = st.text_input("Meta Avaliação:", placeholder="Ex: Responder oralmente...")

# 5. ASSISTENTE
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### <i class='ri-robot-line'></i> Consultor Especialista", unsafe_allow_html=True)
        st.markdown('<div class="home-card" style="padding:15px; border-left:4px solid #004E92;"><p><b>Inteligência Ativa:</b><br>Analiso o perfil do estudante cruzando LBI, Neurociência e BNCC para sugerir um plano assertivo.</p></div>', unsafe_allow_html=True)
        
        status = "✅ PDF Lido" if st.session_state.pdf_text else "⚪ Sem PDF"
        st.caption(f"Status: {status}")
        
        if st.button("✨ Gerar Parecer Completo", type="primary"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome.")
            else:
                with st.spinner("Processando..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Sucesso!")
    with col_ia_right:
        st.markdown("### <i class='ri-file-text-line'></i> Parecer Técnico", unsafe_allow_html=True)
        if st.session_state.dados['ia_sugestao']:
            st.markdown(f'<div style="background:#F8FAFC; padding:20px; border-radius:10px; border:1px solid #E2E8F0; max-height:500px; overflow-y:auto; line-height:1.6;">{st.session_state.dados["ia_sugestao"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with st.expander("✏️ Editar"):
                st.session_state.dados['ia_sugestao'] = st.text_area("Texto:", st.session_state.dados['ia_sugestao'], height=300)
        else:
            st.info("O parecer será gerado aqui.")

# 6. DOCUMENTO (BOTÕES PRÓXIMOS E COLORIDOS)
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        st.success("✅ Documento Pronto para Exportação")
        
        # COLUNAS AJUSTADAS PARA FICAREM PRÓXIMOS
        c1, c2, c3 = st.columns([1, 1, 2])
        
        with c1:
            docx = gerar_docx_final(st.session_state.dados)
            # Botão Secundário (Outline)
            st.download_button("📥 Baixar Word", docx, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="secondary")
        
        with c2:
            pdf = gerar_pdf_nativo(st.session_state.dados)
            # Botão Primário (Sólido)
            st.download_button("📄 Baixar PDF", pdf, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            
    else:
        st.warning("Preencha o nome do estudante.")
    st.markdown("</div>", unsafe_allow_html=True)