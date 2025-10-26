# utils_v4.py minimal utilities
import os, json, io, base64, tempfile
from datetime import datetime
import pandas as pd
from fpdf import FPDF

BASE_JSON='base_militantes.json'
LOCALIDADES_FILE='localidades_luanda_v4.json'

def carregar_base_dados(caminho=BASE_JSON):
    if os.path.exists(caminho):
        try:
            with open(caminho,'r',encoding='utf-8') as f: return json.load(f)
        except: return []
    return []

def guardar_base_dados(base,caminho=BASE_JSON):
    with open(caminho,'w',encoding='utf-8') as f: json.dump(base,f,ensure_ascii=False,indent=2)

def carregar_localidades(caminho=LOCALIDADES_FILE):
    if not os.path.exists(caminho): return {}
    try:
        with open(caminho,'r',encoding='utf-8') as f: return json.load(f)
    except: return {}

def obter_comunas_por_municipio(localidades,municipio):
    if isinstance(localidades,dict): return localidades.get(municipio,[])
    return []

def contar_por_cap(base,cap):
    if not cap: return 0
    return sum(1 for m in base if (m.get('cap') or '').strip().upper()==cap.strip().upper())

def gerar_registro_interno_por_cap(base,cap):
    cap_str=(cap or 'CAP').strip().upper()
    seq=contar_por_cap(base,cap_str)+1
    return f"REG-{cap_str}-{seq:04d}"

def adicionar_militante(base,dados):
    cap=(dados.get('cap') or '').strip().upper()
    if not cap: return base,False,'Nº CAP obrigatório'
    primeiro=(dados.get('primeiro_nome') or '').strip(); ultimo=(dados.get('ultimo_nome') or '').strip()
    nome=f"{primeiro} {ultimo}".strip().upper()
    for m in base:
        if (m.get('cap') or '').strip().upper()==cap:
            if f"{(m.get('primeiro_nome') or '').strip()} {(m.get('ultimo_nome') or '').strip()}".strip().upper()==nome:
                return base,False,'Duplicado detectado'
    dados['registro_interno']=gerar_registro_interno_por_cap(base,cap)
    dados['_created_at']=datetime.now().isoformat(); dados['cap']=cap
    base.append(dados); guardar_base_dados(base)
    return base,True,'Adicionado'

def atualizar_militante_por_cap(base,cap,novos):
    cap=(cap or '').strip().upper(); updated=False
    for i,m in enumerate(base):
        if (m.get('cap') or '').strip().upper()==cap:
            base[i].update(novos); updated=True
    if updated: guardar_base_dados(base)
    return updated

def remover_por_cap(base,cap,nome=None):
    cap=(cap or '').strip().upper(); nova=[]
    for m in base:
        if (m.get('cap') or '').strip().upper()==cap:
            if nome:
                full=f"{(m.get('primeiro_nome') or '')} {(m.get('ultimo_nome') or '')}".strip().upper()
                if full==nome.strip().upper(): continue
                else: nova.append(m)
            else:
                continue
        else: nova.append(m)
    guardar_base_dados(nova); return nova

def importar_dados_excel(base,uploaded):
    try:
        ext=uploaded.name.split('.')[-1].lower()
        if ext=='csv': df=pd.read_csv(uploaded)
        else: df=pd.read_excel(uploaded)
        regs=df.to_dict(orient='records'); added=0
        for r in regs:
            militante={'primeiro_nome':r.get('Nome(s) Próprio(s)') or r.get('primeiro_nome') or '',
                      'ultimo_nome':r.get('Último Nome') or r.get('ultimo_nome') or '',
                      'cap':(r.get('Nº CAP') or r.get('cap') or '').strip().upper(),
                      'telefone':r.get('Telefone') or ''}
            base,ok,_=adicionar_militante(base,militante)
            if ok: added+=1
        return base,added
    except Exception as e:
        print('Erro importar',e); return base,0

def importar_dados_texto(base,texto):
    linhas=[l for l in texto.splitlines() if l.strip()]; added=0
    for linha in linhas:
        partes=linha.split('\t') if '\t' in linha else linha.split('|')
        if len(partes)>=3:
            m={'primeiro_nome':partes[0].strip(),'ultimo_nome':partes[1].strip(),'cap':partes[2].strip().upper(),'telefone':partes[3].strip() if len(partes)>3 else ''}
            base,ok,_=adicionar_militante(base,m)
            if ok: added+=1
    return base,added

def exportar_para_excel(base,caminho='Base_Militantes_Exportada.xlsx'):
    if not base: return None
    import pandas as pd
    df=pd.DataFrame(base); df.to_excel(caminho,index=False); return caminho

class PDFRecibo(FPDF):
    def header(self):
        try:
            if os.path.exists('flag_mpla.png'): self.image('flag_mpla.png',x=10,y=8,w=30)
            if os.path.exists('emblema_mpla.jpg'): self.image('emblema_mpla.jpg',x=170,y=8,w=20)
        except: pass
        self.set_font('Arial','B',14); self.cell(0,8,'MPLA',0,1,'C'); self.ln(6)
    def footer(self):
        self.set_y(-25); self.set_font('Arial','I',9); self.cell(0,6,'MPLA — Servir o Povo e Fazer Angola Crescer',0,1,'C')

def gerar_recibo_pdf_bytes(m):
    pdf=PDFRecibo(); pdf.add_page(); pdf.set_font('Arial','',11)
    campos=[('Registro interno',m.get('registro_interno','')),('Nome completo',f"{m.get('primeiro_nome','')} {m.get('ultimo_nome','')}")]
    for label,val in campos:
        pdf.set_font('Arial','B',10); pdf.cell(50,7,f"{label}:",0,0); pdf.set_font('Arial','',10); pdf.multi_cell(0,7,val or ' ')
    return pdf.output(dest='S').encode('latin-1')
