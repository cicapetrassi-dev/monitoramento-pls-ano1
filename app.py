
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard PLS UFSC", layout="wide")
st.title("🌱 Dashboard de Monitoramento do PLS UFSC (2025–2029)")

csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

if not csv_files:
    st.error("⚠️ Nenhum arquivo .csv encontrado! Faça o upload da planilha no menu lateral esquerdo do Colab e tente novamente.")
    st.stop()

csv_path = csv_files[0]
st.sidebar.success(f"📁 Arquivo lido: {csv_path}")

def make_unique_columns(col_list):
    seen = {}
    new_cols = []
    for c in col_list:
        c_str = str(c).strip() if pd.notna(c) else "Unnamed"
        if c_str == "" or c_str.lower() == "nan":
            c_str = "Unnamed"
        if c_str in seen:
            seen[c_str] += 1
            new_cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            new_cols.append(c_str)
    return new_cols

@st.cache_data
def load_data(path):
    df = None
    for sep in [',', ';']:
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                temp_df = pd.read_csv(path, sep=sep, encoding=enc, on_bad_lines='skip', engine='python')
                if temp_df.shape[1] >= 5:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break

    if df is None:
        df = pd.read_csv(path, on_bad_lines='skip', engine='python')

    df.columns = make_unique_columns(df.columns)

    if 'EIXO' not in df.columns:
        for idx, row in df.iterrows():
            row_vals = [str(v).strip() for v in row.values]
            if 'EIXO' in row_vals:
                df.columns = make_unique_columns(row_vals)
                df = df.iloc[idx + 1:].reset_index(drop=True)
                break

    valid_cols = [c for c in df.columns if not c.startswith('Unnamed') and c.lower() != 'nan']
    if valid_cols:
        df = df[valid_cols]

    # Drop rows where all values are NaN (empty rows)
    df.dropna(how='all', inplace=True)

    status_cols = [c for c in df.columns if 'Status' in str(c)]
    status_col = status_cols[0] if status_cols else df.columns[0]

    df[status_col] = df[status_col].fillna('Sem informação')
    if 'EIXO' in df.columns:
        df['EIXO'] = df['EIXO'].fillna('Não informado')
    else:
        df['EIXO'] = 'Não informado'

    return df, status_col

try:
    df, status_col = load_data(csv_path)

    st.sidebar.header("🔍 Filtros")
    eixos = sorted([str(x) for x in df['EIXO'].dropna().unique()])
    eixos_sel = st.sidebar.multiselect("Eixo Temático:", options=eixos, default=eixos)

    status_opts = sorted([str(x) for x in df[status_col].dropna().unique()])
    status_sel = st.sidebar.multiselect("Status da Ação:", options=status_opts, default=status_opts)

    # Add 'Responsável' filter if 'ENVOLVIDOS' column exists
    if 'ENVOLVIDOS' in df.columns:
        responsaveis = sorted([str(x) for x in df['ENVOLVIDOS'].dropna().unique()])
        responsaveis_sel = st.sidebar.multiselect("Responsável:", options=responsaveis, default=responsaveis)
        df_filtered = df[(df['EIXO'].astype(str).isin(eixos_sel)) & (df[status_col].astype(str).isin(status_sel)) & (df['ENVOLVIDOS'].astype(str).isin(responsaveis_sel))]
    else:
        df_filtered = df[(df['EIXO'].astype(str).isin(eixos_sel)) & (df[status_col].astype(str).isin(status_sel))]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Ações", len(df_filtered))
    c2.metric("Em Andamento", len(df_filtered[df_filtered[status_col] == 'Em andamento']))
    c3.metric("Concluídas", len(df_filtered[df_filtered[status_col] == 'Concluído']))
    c4.metric("Não Iniciadas", len(df_filtered[df_filtered[status_col] == 'Não iniciado']))

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Distribuição por Status")
        fig_pie = px.pie(
            df_filtered, 
            names=status_col, 
            color=status_col,
            color_discrete_map={
                'Concluído': '#2ECC71', 
                'Em andamento': '#F1C40F', 
                'Não iniciado': '#BDC3C7',
                'Sem informação': '#E67E22'
            },
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.subheader("🏛️ Status por Eixo Temático")
        fig_bar = px.histogram(
            df_filtered, 
            x='EIXO', 
            color=status_col,
            color_discrete_map={
                'Concluído': '#2ECC71', 
                'Em andamento': '#F1C40F', 
                'Não iniciado': '#BDC3C7',
                'Sem informação': '#E67E22'
            }
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # New row for additional charts
    if 'ENVOLVIDOS' in df.columns:
        st.markdown("---")
        col_g3, _ = st.columns(2) # Create a new row with two columns, using only the first one for the chart
        with col_g3:
            st.subheader("🧑‍💻 Distribuição por Responsável")
            fig_resp = px.histogram(
                df_filtered, 
                x='ENVOLVIDOS', 
                color=status_col,
                color_discrete_map={
                    'Concluído': '#2ECC71', 
                    'Em andamento': '#F1C40F', 
                    'Não iniciado': '#BDC3C7',
                    'Sem informação': '#E67E22'
                },
                title="Ações por Responsável"
            )
            fig_resp.update_layout(xaxis_title="Responsável", yaxis_title="Número de Ações")
            st.plotly_chart(fig_resp, use_container_width=True)


    st.subheader("📋 Tabela Completa de Ações")
    st.dataframe(df_filtered, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
