import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Funções de Carregamento e Limpeza ---

def carregar_preco_principal(filepath='./data/price/real_price_and_us.xls'):
    """
    Carrega e limpa o arquivo principal de preços diários.
    """
    try:
        # Pula as 3 primeiras linhas, usa vírgula como decimal
        df = pd.read_excel(
            filepath,
            decimal=','
        )
        
        # Renomeia colunas para facilitar
        df.rename(columns={
            'data': 'Data',
            'preco_brl': 'Preco_R',
            'preco_usd': 'Preco_US'
        }, inplace=True)
        
        # Converte colunas para os tipos corretos
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
        
        # Força a conversão para numérico, tratando erros
        # (Às vezes pode vir algo como " - " ou " " que não é número)
        df['Preco_R'] = pd.to_numeric(df['Preco_R'], errors='coerce')
        df['Preco_US'] = pd.to_numeric(df['Preco_US'], errors='coerce')

        # Remove dias em que não houve negociação (NaN)
        df.dropna(subset=['Preco_R', 'Preco_US'], inplace=True)

        # Define a Data como índice
        df.set_index('Data', inplace=True)
        
        print(f"Arquivo '{filepath}' carregado com sucesso.")
        print(df.head())
        return df

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao processar '{filepath}': {e}")
        return None

def carregar_oferta_demanda(filepath='./oferta-e-demanda-milho.xls'):
    """
    Carrega e limpa o arquivo de oferta e demanda (anual).
    """
    try:
        df = pd.read_excel(filepath)
        
        # Extrai o primeiro ano da safra (ex: "2015/16" -> 2015)
        df['Ano'] = df['Safra.Safra'].str.split('/').str[0].astype(int)
        df.set_index('Ano', inplace=True)
        
        # Converte para numérico
        df['Oferta'] = pd.to_numeric(df['Oferta'], errors='coerce')
        df['Demanda'] = pd.to_numeric(df['Demanda'], errors='coerce')
        
        print(f"Arquivo '{filepath}' carregado com sucesso.")
        print(df.head())
        return df

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao processar '{filepath}': {e}")
        return None

def carregar_preco_estado(filepath='./preço-por-estado.xls'):
    """
    Carrega e limpa o arquivo de preço mínimo por estado (anual).
    """
    try:
        df = pd.read_excel(filepath)
        
        # Extrai o ano da vigência (ex: "JAN-2015" -> 2015)
        df['Ano'] = df['Vigência Inicial'].str.split('-').str[1].astype(int)
        
        # Converte preço para numérico
        df['Preço Mínimo'] = pd.to_numeric(df['Preço Mínimo'], errors='coerce')
        
        print(f"Arquivo '{filepath}' carregado com sucesso.")
        print(df.head())
        return df

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao processar '{filepath}': {e}")
        return None

# --- Funções de Plotagem ---

def plotar_preco_tempo(df_preco):
    """
    Gráfico 1: Série temporal do preço do milho em Reais.
    """
    plt.figure(figsize=(14, 7))
    plt.plot(df_preco.index, df_preco['Preco_R'], label='Preço R$/Saca')
    plt.title('Preço Histórico da Saca de Milho (R$)', fontsize=16)
    plt.xlabel('Ano', fontsize=12)
    plt.ylabel('Preço (R$)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('grafico_1_preco_tempo.png')
    print("Gráfico 1 salvo: 'grafico_1_preco_tempo.png'")

def plotar_correlacao_dolar(df_preco):
    """
    Gráfico 2: Heatmap de correlação entre Preço R$, Preço US$ e Taxa de Câmbio.
    """
    # Engenharia de Feature: Calcular Taxa de Câmbio
    # Remove qualquer linha onde Preco_US seja 0 para evitar divisão por zero
    df_preco_filt = df_preco[df_preco['Preco_US'] > 0].copy()
    df_preco_filt['Taxa_Dolar'] = df_preco_filt['Preco_R'] / df_preco_filt['Preco_US']
    
    # Calcula a correlação
    corr = df_preco_filt[['Preco_R', 'Preco_US', 'Taxa_Dolar']].corr()
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
    plt.title('Correlação: Preço do Milho (R$ e US$) vs. Taxa de Câmbio (Dólar)', fontsize=14)
    plt.tight_layout()
    plt.savefig('grafico_2_correlacao_dolar.png')
    print("Gráfico 2 salvo: 'grafico_2_correlacao_dolar.png'")

def plotar_preco_vs_oferta_demanda(df_preco, df_oferta):
    """
    Gráfico 3: Preço médio anual vs. Relação Estoque/Uso.
    """
    # Engenharia de Feature: Relação Estoque/Uso (Stocks-to-Use Ratio)
    # (Oferta - Demanda) / Demanda
    df_oferta['Relacao_Estoque_Uso'] = (df_oferta['Oferta'] - df_oferta['Demanda']) / df_oferta['Demanda']
    
    # Agrega o preço diário para a média anual
    # 'Y' significa 'Year End' (Final do Ano)
    df_preco_anual = df_preco['Preco_R'].resample('Y').mean()
    df_preco_anual = df_preco_anual.to_frame()
    df_preco_anual['Ano'] = df_preco_anual.index.year
    df_preco_anual.set_index('Ano', inplace=True)
    
    # Junta os dados anuais de preço com os de oferta/demanda
    df_merged = df_preco_anual.join(df_oferta, how='inner')
    
    # Remove anos que não estão em ambos os datasets
    df_merged.dropna(inplace=True)
    
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df_merged, x='Relacao_Estoque_Uso', y='Preco_R')
    plt.title('Preço Médio Anual (R$) vs. Relação Estoque/Uso', fontsize=16)
    plt.xlabel('Relação Estoque/Uso (Mais alto = Mais sobra)', fontsize=12)
    plt.ylabel('Preço Médio Anual (R$)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('grafico_3_preco_vs_oferta_demanda.png')
    print("Gráfico 3 salvo: 'grafico_3_preco_vs_oferta_demanda.png'")

def plotar_preco_por_estado(df_estado, ano=2023):
    """
    Gráfico 4: Preço mínimo por Estado/Região para um ano específico.
    """
    df_ano_especifico = df_estado[df_estado['Ano'] == ano].copy()
    
    # Ordena os valores para melhor visualização
    df_ano_especifico.sort_values('Preço Mínimo', ascending=False, inplace=True)
    
    plt.figure(figsize=(15, 8))
    sns.barplot(
        data=df_ano_especifico,
        x='Preço Mínimo',
        y='UF/Regiões amparadas',
        palette='viridis'
    )
    plt.title(f'Preço Mínimo por UF/Região em {ano}', fontsize=16)
    plt.xlabel('Preço Mínimo (R$)', fontsize=12)
    plt.ylabel('UF/Região', fontsize=12)
    plt.tight_layout()
    plt.savefig('grafico_4_preco_por_estado.png')
    print(f"Gráfico 4 salvo: 'grafico_4_preco_por_estado.png'")

# --- Execução Principal ---

if __name__ == "__main__":
    # Garante que os gráficos fiquem com boa aparência
    sns.set_theme(style="whitegrid")
    
    # Define os caminhos dos arquivos
    # (Assume que os arquivos estão na mesma pasta que o script)
    arquivo_preco = './data/price/real_price_and_us.xls'
    arquivo_oferta = './oferta-e-demanda-milho.xls'
    arquivo_estado = './preço-por-estado.xls'

    # Carrega os dados
    df_preco = carregar_preco_principal(arquivo_preco)
    df_oferta = carregar_oferta_demanda(arquivo_oferta)
    df_estado = carregar_preco_estado(arquivo_estado)
    
    # Gera os gráficos
    if df_preco is not None:
        plotar_preco_tempo(df_preco)
        plotar_correlacao_dolar(df_preco)

    if df_preco is not None and df_oferta is not None:
        plotar_preco_vs_oferta_demanda(df_preco, df_oferta)

    if df_estado is not None:
        # Tenta plotar o ano mais recente disponível, ou 2023 como padrão
        ano_recente = df_estado['Ano'].max()
        if pd.isna(ano_recente):
            ano_recente = 2023
        plotar_preco_por_estado(df_estado, ano=int(ano_recente))

    print("\nAnálise exploratória concluída! Verifique os arquivos .png gerados.")
