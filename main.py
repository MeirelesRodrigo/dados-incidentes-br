import pandas as pd
import folium
from folium.plugins import HeatMap

# -- CARREGAMENTO DOS DADOS -- 
data = pd.read_csv("datatran2024.csv", sep=";", encoding="latin1")

# -- REMOVENDO COLUNAS DESNCESSARIAS -- 
data = data.drop(columns=["id","dia_semana","municipio","classificacao_acidente","fase_dia","sentido_via","condicao_metereologica","tipo_pista","tracado_via","uso_solo","pessoas","veiculos","regional","delegacia","uop"])

# -- TRATAMENTO DOS DADOS -- 

# -- TRATANDO DATA --
data['data'] = pd.to_datetime(data['data_inversa'])
data['ano'] = data['data'].dt.year
data['mes'] = data['data'].dt.month
data['dia'] = data['data'].dt.day
data = data.drop(columns=['data_inversa'])
# -----------------------------

# -- TRATANDO HORARIO -- 
data['horario'] = pd.to_datetime(data['horario'], format="%H:%M:%S").dt.time
data['hora'] = pd.to_datetime(data['horario'], format='%H:%M:%S').dt.hour
# -----------------------------

# -- CONVERTENDO VALORES PARA FLOAT --
data[['km', 'mortos', 'feridos_graves', 'feridos_leves', 'ilesos', 'ignorados']].info()
data['km'] = data['km'].str.replace(",",".").astype(float)
# -----------------------------

# -- REMOVENDO COORDENADAS INVÁLIDAS -- 
# pd.to_numeric(data['latitude'], errors='coerce')
data = data[(data['latitude'] != 0) & (data['longitude'] != 0)]
data = data.dropna(subset=['latitude', 'longitude'])
# -----------------------------

# -- CRIANDO TOTAL DE VITIMAS PARA O MAP -- 
data['total_vitimas'] = (data['mortos'] + data['feridos_leves'] + data['feridos_graves'])
# -----------------------------

data = data.drop_duplicates(subset=['data','hora','latitude','longitude','tipo_acidente'])
# -----------------------------

# ETAPA 02

# NOME DO MES
data['mes_nome'] = data['data'].dt.month_name(locale='pt_BR')

# PERIODO DO DIA
def periodo_do_dia(h):
    if 5 <= h < 12:
        return 'Manhã'
    elif 12 <= h < 18:
        return 'Tarde'
    elif 18 <= h < 24:
        return 'Noite'
    else:
        return 'Madrugada'
    
data['periodo_dia'] = data['hora'].apply(periodo_do_dia)

# FAIXA HORARIA
def faixa(h):
    if h < 6:  return "0–6"
    if h < 12: return "6–12"
    if h < 18: return "12–18"
    return "18–24"

data['faixa_horaria'] = data['hora'].apply(faixa)

# VALIDAR COORDENADAS BR
data = data[
    (data['latitude'] >= -33) & (data['latitude'] <= 5) &
    (data['longitude'] >= -74) & (data['longitude'] <= -28)
]

# CRIANDO COLUNA DE RAIO DO PONTO

data['raio_mapa'] = data['total_vitimas'] * 2

data.loc[data['raio_mapa'] < 4, 'raio_mapa'] = 4
data.loc[data['raio_mapa'] > 60, 'raio_mapa'] = 60

# SEVERIDAD3E 
data['severidade'] = (
    3 * data['mortos'] +
    2 * data['feridos_graves'] +
    1 * data['feridos_leves']
) # ILESOS E IGNORADOS NAO AUMENTAM A SEVERIDADE

# ----------------------

data['tipo_acidente'] = data['tipo_acidente'].str.title().str.strip()
data['causa_acidente'] = data['causa_acidente'].str.title().str.strip()

colunas_mapa = [
    'data', 'ano', 'mes', 'mes_nome', 'dia',
    'hora', 'faixa_horaria', 'periodo_dia',
    'uf', 'tipo_acidente', 'causa_acidente',
    'latitude', 'longitude',
    'mortos', 'feridos_graves', 'feridos_leves', 'ilesos',
    'total_vitimas', 'raio_mapa', 'severidade'
]

dataset_mapa = data[colunas_mapa].copy()

# ETAPA 03
# ANALISE ESTATÍSTICA

# TOTAL DE ACIDENTES POR UF
acidentes_por_uf = dataset_mapa['uf'].value_counts().reset_index()
acidentes_por_uf.columns = ['UF', 'total_acidente']

# TIPOS DE ACIDENTES MAIS COMUNS
tipos_acidentes = dataset_mapa['tipo_acidente'].value_counts().reset_index()
tipos_acidentes.columns = ['Tipo de acidente', 'Total']

# CAUSAS MAIS COMUNS
dataset_mapa
causa_acidentes = dataset_mapa['causa_acidente'].value_counts().reset_index()
causa_acidentes.columns = ['Causa', 'Total']
causa_acidentes

# ACIDENTES POR PERIODO DO DIA
periodos = dataset_mapa['periodo_dia'].value_counts().reset_index()
periodos.columns = ['Período do dia', 'Total']
periodos

# ACIDENTES POR FAIXA HORARIA
faixa_horaria = dataset_mapa['faixa_horaria'].value_counts().reset_index()
faixa_horaria.columns = ['Faixa Horária', 'Total']
faixa_horaria.sort_values('Faixa Horária')

# ACIDENTES POR MÊS
acidentes_mes = dataset_mapa['mes_nome'].value_counts().reset_index()
acidentes_mes.columns = ['Mês', 'Total']
acidentes_mes

# TOTAL DE ACIDENTES POR ESTADO
vitimas_por_uf = dataset_mapa.groupby('uf')['total_vitimas'].sum().reset_index()
vitimas_por_uf.columns = ['UF', 'Total de Vítimas']
vitimas_por_uf

# SEVERIDADE MÉDIA POR ESTADO
severidade_uf = dataset_mapa.groupby('uf')['severidade'].mean().reset_index()
severidade_uf.columns = ['UF', 'Severidade Média']
severidade_uf

# ============================
# 🌎 1. CONFIGURAR MAPA BASE

# Centraliza o mapa no Brasil
mapa = folium.Map(
    location=[-15.788497, -47.879873],  # centro aproximado
    zoom_start=5,
    tiles="cartodbpositron"
)

# ============================
# 🔥 2. MAPA DE CALOR (Heatmap)

heat_data = dataset_mapa[['latitude', 'longitude', 'severidade']].values.tolist()

HeatMap(
    heat_data,
    radius=12,
    blur=18,
    max_val=dataset_mapa['severidade'].max(),
    min_opacity=0.2
).add_to(mapa)


# ============================
# 🎯 3. PONTOS INDIVIDUAIS

for _, row in dataset_mapa.iterrows():

    # COR DA BOLINHA
    if row['severidade'] == 0:
        cor = "green"
    elif row['severidade'] <= 3:
        cor = "yellow"
    elif row['severidade'] <= 6:
        cor = "orange"
    else:
        cor = "red"

    # POPUP COM INFORMAÇÕES
    popup = folium.Popup(f"""
    <b>Data:</b> {row['data'].date()}<br>
    <b>Horário:</b> {row['hora']}h ({row['periodo_dia']})<br>
    <b>Tipo:</b> {row['tipo_acidente']}<br>
    <b>Causa:</b> {row['causa_acidente']}<br>
    <b>UF:</b> {row['uf']}<br><br>

    <b>Mortos:</b> {row['mortos']}<br>
    <b>Feridos graves:</b> {row['feridos_graves']}<br>
    <b>Feridos leves:</b> {row['feridos_leves']}<br>
    <b>Ilesos:</b> {row['ilesos']}<br><br>

    <b>Total vítimas:</b> {row['total_vitimas']}<br>
    <b>Severidade:</b> {row['severidade']}<br>
    """, max_width=350)

    # CÍRCULO
    folium.Circle(
    location=[row['latitude'], row['longitude']],
    radius=row['raio_mapa'] * 100,
    color=cor,
    fill=True,
    fill_color=cor,
    fill_opacity=0.35,
    weight=1,
    popup=popup       
).add_to(mapa)



# ============================
# 💾 4. SALVAR MAPA

mapa.save("mapa_acidentes_corrigidov2.html")

print("Mapa gerado com sucesso!")