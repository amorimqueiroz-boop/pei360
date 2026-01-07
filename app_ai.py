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

# --- ESTILO VISUAL PREMIUM (BASEADO NA REF. COC) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    :root { --brand-primary: #00796B; /* Verde Profissional da Ref */ --brand-secondary: #004E92; --bg-card: #FFFFFF; }
    
    /* Inputs Modernos */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important; border: 1px solid #E2E8F0 !important; background-color: #FFFFFF;
    }
    
    /* Upload Clean */
    div[data-testid="stFileUploader"] section { 
        background-color: #F8FAFC; border: 1px dashed #A0AEC0; border-radius: 12px;
    }

    /* Cards Estilo Dashboard */
    .action-card {
        background-color: white; 
        padding: 25px; 
        border-radius: 16px; 
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02); 
        margin-bottom: 20px;
    }
    .action-card h4 { 
        color: var(--brand-secondary); font-weight: 800; font-size: 1.1rem; 
        display: flex; align-items: center; gap: 10px; margin-bottom: 15px;
    }
    .action-card p { font-size: 0.9rem; color: #718096; margin-bottom: 15px; }
    
    /* Botões */
    .stButton>button {
        background-color: var(--brand-secondary); color: white; border-radius: 10px;
        font-weight: 700; height: 3.5em; width: 100%; border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
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

# --- INTEELIGÊNCIA ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        serie = dados['serie'] if dados['serie'] else ""
        
        # Contextualização BNCC
        if "Infantil" in serie:
            foco_bncc = "Campos de Experiência"
        else:
            foco_bncc = "Habilidades Essenciais (Códigos Alfanuméricos)"

        prompt_sistema = f"""
        Atue como Coordenador Pedagógico Inclusivo.
        Analise o caso com base em: LBI 13.146, Neurociência Cognitiva e BNCC ({foco_bncc}).
        """
        
        contexto_extra = f"\n📄 LAUDO:{contexto_pdf[:3000]}" if contexto_pdf else ""
        nasc_str = str(dados.get('nasc', ''))
        
        prompt_usuario = f"""
        Estudante: {dados['nome']} | Série: {serie} | Idade: {nasc_str}
        Diag: {dados['diagnostico']} | Hiperfoco: {dados['hiperfoco']}
        {contexto_extra}
        
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        Estratégias Já Selecionadas: 
        - Acesso: {', '.join(dados['estrategias_acesso'])}
        - Metodologia: {', '.join(dados['estrategias_ensino'])}
        - Avaliação: {', '.join(dados['estrategias_avaliacao'])}
        
        PARECER TÉCNICO (Estrutura Obrigatória):
        1. 🧠 Conexão Neural: Como o Hiperfoco pode ser a "porta de entrada" para o conteúdo.
        2. 🎯 Foco Curricular ({foco_bncc}): Selecione 1 objetivo central da série e mostre como adaptá-lo.
        3. 💡 Refinamento de Estratégias: Valide as escolhas da escola e sugira 1 ajuste fino.
        """
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro DeepSeek: {str(e)}"

# --- GERADORES DE DOCUMENTOS ---
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

    # 1. Identificação
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("1. IDENTIFICAÇÃO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    nasc = dados.get('nasc'); d_nasc = nasc.strftime('%d/%m/%Y') if nasc else "-"
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nNascimento: {d_nasc}\nDiagnóstico: {dados['diagnostico']}"))
    pdf.ln(3)

    # 2. Mapeamento
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("2. BARREIRAS E POTENCIALIDADES"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Hiperfoco: {dados['hiperfoco']}"))
    b_total = dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social']
    if b_total: pdf.multi_cell(0, 7, txt(f"Barreiras Mapeadas: {limpar_para_pdf(', '.join(b_total))}"))
    pdf.ln(3)

    # 3. Plano de Ação (Nova Estrutura)
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("3. PLANO DE AÇÃO EDUCACIONAL"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    
    if dados['estrategias_acesso']:
        pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt("Organização e Acesso:"), 0, 1); pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, txt(limpar_para_pdf(', '.join(dados['estrategias_acesso']))))
        if dados['meta_acesso']: pdf.multi_cell(0, 7, txt(f"Meta Prioritária: {dados['meta_acesso']}"))
        pdf.ln(2)

    if dados['estrategias_ensino']:
        pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt("Metodologia de Ensino:"), 0, 1); pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, txt(limpar_para_pdf(', '.join(dados['estrategias_ensino']))))
        if dados['meta_ensino']: pdf.multi_cell(0, 7, txt(f"Meta Prioritária: {dados['meta_ensino']}"))
        pdf.ln(2)

    if dados['estrategias_avaliacao']:
        pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, txt("Avaliação Diferenciada:"), 0, 1); pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, txt(limpar_para_pdf(', '.join(dados['estrategias_avaliacao']))))
        if dados['meta_avaliacao']: pdf.multi_cell(0, 7, txt(f"Meta Prioritária: {dados['meta_avaliacao']}"))
        pdf.ln(2)

    # 4. Parecer IA
    if dados['ia_sugestao']:
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("4. PARECER TÉCNICO ESPECIALISTA"), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(limpar_para_pdf(dados['ia_sugestao'])))

    pdf.ln(15); pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.cell(0, 10, txt("Coordenação Pedagógica"), 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

def gerar_docx_final(dados):
    doc = Document(); style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    
    doc.add_heading('Plano de Ação', level=1)
    doc.add_paragraph(f"Acesso: {', '.join(dados['estrategias_acesso'])}")
    doc.add_paragraph(f"Ensino: {', '.join(dados['estrategias_ensino'])}")
    doc.add_paragraph(f"Avaliação: {', '.join(dados['estrategias_avaliacao'])}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Parecer Técnico', level=1)
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
        # NOVOS CAMPOS DO PLANO DE AÇÃO
        'estrategias_acesso': [], 'meta_acesso': '',
        'estrategias_ensino': [], 'meta_ensino': '',
        'estrategias_avaliacao': [], 'meta_avaliacao': '',
        'ia_sugestao': ''
    }

# PATCH DE SEGURANÇA (Para não quebrar sessões antigas)
for key in ['estrategias_ensino', 'estrategias_avaliacao', 'meta_acesso', 'meta_ensino', 'meta_avaliacao']:
    if key not in st.session_state.dados:
        st.session_state.dados[key] = [] if 'estrategias' in key else ''
if 'nasc' not in st.session_state.dados: st.session_state.dados['nasc'] = None
if 'rede_apoio' not in st.session_state.dados: st.session_state.dados['rede_apoio'] = []
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# --- SIDEBAR ---
with st.sidebar:
    logo = encontrar_arquivo_logo()
    if logo: st.image(logo, width=120)
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']; st.success("✅ Chave Segura")
    else: api_key = st.text_input("Chave API:", type="password")
    st.markdown("---"); st.info("Versão 13.0 | Experience UI")

# --- CABEÇALHO ---
logo = encontrar_arquivo_logo()
header_html = ""
if logo:
    mime = "image/png" if logo.lower().endswith("png") else "image/jpeg"
    b64 = get_base64_image(logo)
    img_tag = f'<img src="data:{mime};base64,{b64}" style="max-height: 85px; width: auto; margin-right: 20px;">'
    text_div = '<div style="border-left: 2px solid #CBD5E0; padding-left: 20px; height: 60px; display: flex; align-items: center;"><p style="margin: 0; color: #4A5568; font-weight: 500; font-size: 1.1rem;">Planejamento Educacional Individualizado</p></div>'
    header_inner = f'<div style="display: flex; align-items: center; height: 100%;">{img_tag}{text_div}</div>'
else:
    header_inner = '<div style="display: flex; align-items: center;"><i class="ri-global-line" style="font-size: 3.5rem; margin-right: 20px; color: #004E92;"></i><div><h1 style="color: #004E92; margin: 0; font-weight: 800; font-size: 2.5rem; line-height: 1;">PEI 360º</h1><p style="margin: 5px 0 0 0; color: #4A5568;">Sistema de Inclusão</p></div></div>'

st.markdown(f"""
<div style="padding: 15px 25px; background: linear-gradient(90deg, #FFFFFF 0%, #E3F2FD 100%); border-radius: 15px; border-left: 8px solid #004E92; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; min-height: 100px; display: flex; align-items: center;">
    {header_inner}
</div>
""", unsafe_allow_html=True)

abas = ["Início", "Estudante", "Mapeamento", "Plano de Ação", "Assistente de IA", "Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME
with tab1:
    st.markdown("### <i class='ri-dashboard-line'></i> Ecossistema de Inclusão", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="action-card"><h4><i class="ri-book-open-line"></i> O que é o PEI?</h4><p>Não é apenas um formulário. É um <b>mapa vivo</b> que transforma a matrícula em inclusão real.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="action-card"><h4><i class="ri-scales-3-line"></i> Legislação (Res. Dez/2025)</h4><p>O PEI é <b>obrigatório</b> para estudantes com barreiras de aprendizagem, independente de laudo médico fechado.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="action-card"><h4><i class="ri-brain-line"></i> Neurociência</h4><p>Foco nas <b>Funções Executivas</b>. Entendemos "como" o cérebro processa a informação.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="action-card"><h4><i class="ri-compass-3-line"></i> Conexão BNCC</h4><p>Ed. Infantil: <b>Campos de Experiência</b>.<br>Fund./Médio: <b>Habilidades Essenciais</b>.</p></div>', unsafe_allow_html=True)

# 2. ESTUDANTE
with tab2:
    st.info("Dossiê do Estudante.")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    val_nasc = st.session_state.dados.get('nasc')
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", val_nasc, format="DD/MM/YYYY")
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione...")
    
    st.markdown("---")
    st.markdown("##### <i class='ri-history-line'></i> Contexto Escolar e Familiar", unsafe_allow_html=True)
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Escolas anteriores...")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="Expectativas...")

    st.markdown("---")
    st.markdown("##### <i class='ri-stethoscope-line'></i> Clínico e Apoio", unsafe_allow_html=True)
    c_diag, c_rede = st.columns(2)
    st.session_state.dados['diagnostico'] = c_diag.text_input("Diagnóstico Clínico (ou em investigação)", st.session_state.dados['diagnostico'])
    val_rede = st.session_state.dados.get('rede_apoio', [])
    st.session_state.dados['rede_apoio'] = c_rede.multiselect("Rede de Apoio:", ["Psicólogo", "Fonoaudiólogo", "Neuropediatra", "Terapeuta Ocupacional", "Psicopedagogo", "AT"], default=val_rede, placeholder="Selecione...")
    
    st.write("")
    with st.expander("📂 Anexar Laudo Médico (PDF) - Opcional"):
        uploaded_file = st.file_uploader("Arraste o arquivo aqui", type="pdf", key="uploader_tab2")
        if uploaded_file is not None:
            texto = ler_pdf(uploaded_file)
            if texto: st.session_state.pdf_text = texto; st.success("✅ Documento Lido!")

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

# 4. PLANO DE AÇÃO ROBUSTO (NOVO)
with tab4:
    st.markdown("### <i class='ri-checkbox-circle-line'></i> Definição de Estratégias", unsafe_allow_html=True)
    st.write("Selecione os recursos e defina uma meta prioritária para cada pilar.")
    
    col_a, col_b = st.columns(2)
    
    # CARD 1: Organização e Acesso
    with col_a:
        st.markdown("""
        <div class="action-card">
            <h4><i class="ri-layout-masonry-line"></i> 1. Organização e Acesso</h4>
            <p>Mudanças no ambiente físico, rotina e gestão do tempo.</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Recursos de Acesso:", 
            ["Tempo estendido (+25%)", "Ledor e Escriba", "Material Ampliado (Arial 24)", "Uso de Tablet/Notebook", "Local Silencioso para Prova", "Pausas Monitoradas", "Fone de Cancelamento de Ruído", "Rotina Visual na Mesa"], 
            placeholder="Selecione..."
        )
        st.session_state.dados['meta_acesso'] = st.text_input("🎯 Meta Prioritária (Acesso):", placeholder="Ex: Aumentar tempo de permanência em sala...")

    # CARD 2: Metodologia e Currículo
    with col_b:
        st.markdown("""
        <div class="action-card">
            <h4><i class="ri-pencil-ruler-2-line"></i> 2. Metodologia de Ensino</h4>
            <p>Como o conteúdo será apresentado e trabalhado.</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.dados['estrategias_ensino'] = st.multiselect(
            "Estratégias de Ensino:", 
            ["Fragmentação de Tarefas", "Pistas Visuais de Apoio", "Mapa Mental Prévio", "Mediação Individualizada", "Redução de Volume (Exercícios)", "Ensino Multisensorial", "Antecipação de Conteúdo"], 
            placeholder="Selecione..."
        )
        st.session_state.dados['meta_ensino'] = st.text_input("🎯 Meta Prioritária (Ensino):", placeholder="Ex: Realizar 5 questões com autonomia...")

    # CARD 3: Avaliação (Ocupa largura total embaixo)
    st.markdown("---")
    c_aval, c_resumo = st.columns([1, 1])
    
    with c_aval:
        st.markdown("""
        <div class="action-card">
            <h4><i class="ri-file-list-3-line"></i> 3. Avaliação Diferenciada</h4>
            <p>Formas alternativas de demonstrar conhecimento.</p>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.dados['estrategias_avaliacao'] = st.multiselect(
            "Adaptação de Provas:", 
            ["Prova Oral", "Prova sem Distratores Visuais", "Consulta a Roteiro/Fórmulas", "Avaliação por Projeto/Trabalho", "Enunciados Curtos e Diretos", "Correção Flexível (Foco no Conteúdo)"], 
            placeholder="Selecione..."
        )
        st.session_state.dados['meta_avaliacao'] = st.text_input("🎯 Meta Prioritária (Avaliação):", placeholder="Ex: Responder oralmente com segurança...")

    with c_resumo:
        # Resumo Visual Rápido
        if st.session_state.dados['estrategias_acesso'] or st.session_state.dados['estrategias_ensino']:
            st.info("✅ Resumo das Adaptações:\n\n" + 
                    f"• Acesso: {len(st.session_state.dados['estrategias_acesso'])} itens\n" + 
                    f"• Ensino: {len(st.session_state.dados['estrategias_ensino'])} itens\n" + 
                    f"• Avaliação: {len(st.session_state.dados['estrategias_avaliacao'])} itens")

# 5. ASSISTENTE
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### <i class='ri-robot-line'></i> Consultor Especialista", unsafe_allow_html=True)
        st.markdown("""
        <div class="action-card">
            <h4><i class="ri-lightbulb-flash-line"></i> Inteligência Pedagógica</h4>
            <p>Minha análise cruza LBI, Neurociência e BNCC.</p>
        </div>
        """, unsafe_allow_html=True)
        
        status_anexo = "✅ PDF Anexado" if st.session_state.pdf_text else "⚪ Sem anexo"
        st.caption(f"Contexto: {status_anexo}")
        
        if st.button("✨ Gerar Parecer Completo"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome.")
            else:
                with st.spinner("Processando..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Sucesso!")
    with col_ia_right:
        st.markdown("### <i class='ri-file-text-line'></i> Parecer Técnico", unsafe_allow_html=True)
        if st.session_state.dados['ia_sugestao']:
            st.markdown(f"""
            <div style="background-color:#F8FAFC; padding:20px; border-radius:10px; border:1px solid #E2E8F0; max-height:500px; overflow-y:auto; font-size:0.95rem; line-height:1.6;">
                {st.session_state.dados['ia_sugestao'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            with st.expander("✏️ Editar Texto"):
                st.session_state.dados['ia_sugestao'] = st.text_area("Edição:", st.session_state.dados['ia_sugestao'], height=300)
        else:
            st.info("O parecer será gerado aqui.")

# 6. DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        c1, c2 = st.columns(2)
        with c1:
            docx = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar Word (.docx)", docx, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c2:
            pdf = gerar_pdf_nativo(st.session_state.dados)
            st.download_button("📄 Baixar PDF Oficial", pdf, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf")
    else:
        st.warning("Preencha o nome do estudante.")
    st.markdown("</div>", unsafe_allow_html=True)