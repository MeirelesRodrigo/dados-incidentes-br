import pandas as pd

# -- CARREGAMENTO DOS DADOS -- 
data = pd.read_csv("datatran2024.csv", sep=";", encoding="latin1")
# -----------------------------

# -- REMOVENDO COLUNAS DESNCESSARIAS -- 
data = data.drop(columns=["id","dia_semana","municipio","classificacao_acidente","fase_dia","sentido_via","condicao_metereologica","tipo_pista","tracado_via","uso_solo","pessoas","veiculos","regional","delegacia","uop"])
# -----------------------------

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
data['total_vitimas'] = (data['mortos'] + data['feridos_leves'] + data['feridos_graves'] + data['ilesos'] + data['ignorados'] + data['feridos'])
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
data = data[(data['latitude'] >= -34 ) & (data['latitude'] <= 6) & (data['latitude'] >= -75) & (data['longitude'] <= -28) ]


# CRIANDO COLUNA DE RAIO DO PONTO
data['total_vitimas']
data['raio_mapa'] = data['total_vitimas'] * 2
data.loc[data['raio_mapa'] == 0, 'raio_mapa'] = 2

# SEVERIDAD3E 
data['severidade'] = (3*data['mortos'] + 2*data['feridos_graves'] + 1*data['feridos_leves']) # ILESOS E IGNORADOS NAO AUMENTAM A SEVERIDADE

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