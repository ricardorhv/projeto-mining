import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob # Para encontrar todos os arquivos de clima
import numpy as np

# --- Funções de Carregamento (Baseadas na sua edição) ---

def carregar_preco_principal(filepath='./data/price/real_price_and_us.xls'):
    """
    Carrega e limpa o arquivo principal de preços diários.
    Usa 'read_excel' pois o arquivo é .xls
    """
    try:
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
        
        # Força a conversão para numérico
        df['Preco_R'] = pd.to_numeric(df['Preco_R'], errors='coerce')
        df['Preco_US'] = pd.to_numeric(df['Preco_US'], errors='coerce')
        df.dropna(subset=['Preco_R', 'Preco_US'], inplace=True)
        df.set_index('Data', inplace=True)
        
        print(f"Arquivo '{filepath}' carregado com sucesso.")
        return df

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        print("Por favor, verifique o caminho e nome do arquivo de preço.")
        return None
    except Exception as e:
        print(f"ERRO ao processar '{filepath}': {e}")
        return None

def carregar_oferta_demanda(filepath='./oferta-e-demanda-milho.xls'):
    """
    Carrega e limpa o arquivo de oferta e demanda (anual).
    Usa 'read_excel' pois o arquivo é .xls
    """
    try:
        df = pd.read_excel(filepath)
        
        # Remove a linha de cabeçalho "Safra.Safra" se ela foi lida como dados
        if 'Safra.Safra' in df.columns:
            # Assume que a primeira linha é o cabeçalho correto
            pass
        else:
             # Se o cabeçalho estiver errado, recarrega
             df = pd.read_excel(filepath, header=0)

        # Extrai o primeiro ano da safra (ex: "2015/16" -> 2015)
        df['Ano'] = df['Safra.Safra'].astype(str).str.split('/').str[0].astype(int)
        df.set_index('Ano', inplace=True)
        
        df['Oferta'] = pd.to_numeric(df['Oferta'], errors='coerce')
        df['Demanda'] = pd.to_numeric(df['Demanda'], errors='coerce')
        
        print(f"Arquivo '{filepath}' carregado com sucesso.")
        return df

    except FileNotFoundError:
        print(f"ERRO: Arquivo '{filepath}' não encontrado.")
        return None
    except Exception as e:
        print(f"ERRO ao processar '{filepath}': {e}")
        return None

# --- Nova Função de Carregamento de Clima (Unificada) ---

def carregar_inmet_unificado(pasta_csvs='./data_tempo'):
    """
    Carrega TODOS os arquivos CSV do INMET de uma pasta,
    limpa, agrega por dia e unifica em um único DataFrame.
    """
    
    # Encontra todos os arquivos CSV do INMET na pasta especificada
    padrao_arquivo = os.path.join(pasta_csvs, 'INMET_*.CSV')
    all_files = glob.glob(padrao_arquivo)
    
    if not all_files:
        print(f"ERRO: Nenhum arquivo CSV do INMET encontrado em '{pasta_csvs}' com o padrão 'INMET_*.CSV'.")
        return None

    print(f"Encontrados {len(all_files)} arquivos de clima. Processando...")
    
    all_dfs = []

    for filepath in all_files:
        try:
            # Tenta identificar a estação pelo nome do arquivo
            filename = os.path.basename(filepath)
            station = 'Sinop' if 'SINOP' in filename else 'Sorriso'
            
            # Carrega o CSV. 'latin-1' é comum para arquivos do INMET com '?'
            df = pd.read_csv(
                filepath,
                delimiter=';',
                skiprows=8,
                decimal=',',
                encoding='latin-1'
            )
            
            # --- Encontra as colunas corretas (os nomes mudam) ---
            col_data = next((col for col in df.columns if 'DATA' in col.upper() and 'YYYY' in col.upper()), None)
            if col_data is None: # Tenta o formato novo (2019+)
                col_data = next((col for col in df.columns if col.upper() == 'DATA'), None)
            
            col_hora = next((col for col in df.columns if 'HORA' in col.upper()), None)
            col_precip = next((col for col in df.columns if 'PRECIPITAÇÃO' in col.upper()), None)
            col_temp = next((col for col in df.columns if 'TEMPERATURA DO AR' in col.upper()), None)

            if not all([col_data, col_hora, col_precip, col_temp]):
                print(f"Aviso: Pulando arquivo '{filename}'. Colunas essenciais não encontradas.")
                continue

            # Seleciona e renomeia
            df_clean = df[[col_data, col_hora, col_precip, col_temp]].copy()
            df_clean.columns = ['Data', 'Hora', 'Precipitacao', 'Temperatura']
            
            # --- Limpeza dos dados ---
            # 1. Limpa datas e horas
            df_clean['Data'] = df_clean['Data'].str.replace('/', '-')
            df_clean['Hora'] = df_clean['Hora'].astype(str).str.replace(' UTC', '').str.zfill(4)
            
            # 2. Cria datetime unificado
            df_clean['Datetime'] = pd.to_datetime(
                df_clean['Data'] + ' ' + df_clean['Hora'],
                format='%Y-%m-%d %H%M',
                errors='coerce'
            )
            df_clean.dropna(subset=['Datetime'], inplace=True)
            df_clean.set_index('Datetime', inplace=True)
            
            # 3. Limpa dados numéricos
            df_clean['Precipitacao'] = pd.to_numeric(df_clean['Precipitacao'], errors='coerce')
            df_clean['Temperatura'] = pd.to_numeric(df_clean['Temperatura'], errors='coerce')
            
            # -9999 é o código do INMET para dado faltante
            df_clean['Precipitacao'].replace(-9999, 0.0, inplace=True)
            df_clean['Precipitacao'].fillna(0.0, inplace=True) # Preenche lacunas com 0 (não choveu)
            
            df_clean['Temperatura'].replace(-9999, np.nan, inplace=True)
            df_clean['Temperatura'].fillna(method='ffill', inplace=True) # Preenche lacunas de temp com a última válida
            
            # 4. Agrega dados HORÁRIOS para DIÁRIOS
            df_daily = df_clean.resample('D').agg({
                'Precipitacao': 'sum',
                'Temperatura': 'mean'
            })
            
            df_daily['Estacao'] = station
            all_dfs.append(df_daily)

        except Exception as e:
            print(f"ERRO ao processar o arquivo '{filename}': {e}")
    
    if not all_dfs:
        print("Nenhum arquivo de clima foi processado com sucesso.")
        return None
        
    # Concatena todos os dataframes diários
    df_clima_completo = pd.concat(all_dfs)
    
    # --- Pivota os dados ---
    # Queremos colunas: Precipitacao_Sinop, Temperatura_Sinop, etc.
    df_clima_pivot = df_clima_completo.pivot_table(
        index=df_clima_completo.index,
        columns='Estacao',
        values=['Precipitacao', 'Temperatura']
    )
    
    # Arruma os nomes das colunas (ex: de ('Precipitacao', 'Sinop') para 'Precipitacao_Sinop')
    df_clima_pivot.columns = [f'{val}_{stat}' for val, stat in df_clima_pivot.columns]
    
    print("Dados de clima unificados e agregados por dia:")
    print(df_clima_pivot.head())
    return df_clima_pivot

# --- Nova Função de Plotagem ---

def plotar_correlacao_master(df, filename='grafico_master_correlacao.png'):
    """
    Plota o mapa de calor de correlação final do DataFrame mestre.
    """
    plt.figure(figsize=(15, 10))
    corr = df.corr()
    sns.heatmap(
        corr,
        annot=True,
        cmap='coolwarm',
        fmt='.2f',
        linewidths=0.5,
        annot_kws={"size": 8}
    )
    plt.title('Mapa de Calor: Correlação de Todas as Variáveis (Mensal)', fontsize=16)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Gráfico de correlação mestre salvo em: '{filename}'")

# --- Execução Principal (ETL e Criação do Master DF) ---

if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    
    # --- 1. CARREGAR OS DADOS ---
    
    # ATENÇÃO: Verifique se os caminhos estão corretos!
    path_preco = './data/price/real_price_and_us.xls'
    path_oferta = './oferta-e-demanda-milho.xls'
    # Assume que os CSVs do INMET estão na mesma pasta do script
    path_clima = './data_tempo' 
    
    df_preco_diario = carregar_preco_principal(path_preco)
    df_oferta_anual = carregar_oferta_demanda(path_oferta)
    df_clima_diario = carregar_inmet_unificado(path_clima)

    if df_preco_diario is None or df_oferta_anual is None or df_clima_diario is None:
        print("\n!!! ERRO FATAL: Um ou mais arquivos de dados não puderam ser carregados. Encerrando. !!!")
        print("Por favor, verifique os nomes e caminhos dos arquivos.")
    else:
        # --- 2. TRANSFORMAR (AGREGAR PARA MENSAL) ---
        
        print("\nIniciando agregação mensal...")
        
        # Agrega Preço Diário para Média Mensal ('MS' = Month Start)
        df_preco_mensal = df_preco_diario[['Preco_R', 'Preco_US']].resample('MS').mean()
        
        # Agrega Clima Diário para Mensal
        # Chuva = Soma total do mês
        # Temperatura = Média do mês
        df_clima_mensal = df_clima_diario.resample('MS').agg({
            'Precipitacao_Sinop': 'sum',
            'Precipitacao_Sorriso': 'sum',
            'Temperatura_Sinop': 'mean',
            'Temperatura_Sorriso': 'mean'
        })
        
        # Prepara Oferta/Demanda Anual para Mensal
        # Cria a feature de "Relação Estoque/Uso"
        df_oferta_anual['Relacao_Estoque_Uso'] = (df_oferta_anual['Oferta'] - df_oferta_anual['Demanda']) / df_oferta_anual['Demanda']
        # Converte o índice 'Ano' (int) para Datetime
        df_oferta_anual.index = pd.to_datetime(df_oferta_anual.index, format='%Y')
        # Reamostra para mensal, preenchendo os 12 meses do ano com o valor daquele ano
        df_oferta_mensal = df_oferta_anual.resample('MS').ffill()
        # Garante que preenche todos os meses até o fim dos dados
        df_oferta_mensal = df_oferta_mensal.reindex(df_preco_mensal.index, method='ffill')
        
        
        # --- 3. COMBINAR (CRIAR MASTER DATAFRAME) ---
        
        print("Combinando todos os dados em um DataFrame Mestre...")
        
        # Junta Preço e Clima
        master_df = df_preco_mensal.join(df_clima_mensal)
        
        # Junta com Oferta/Demanda
        master_df = master_df.join(df_oferta_mensal[['Relacao_Estoque_Uso']])
        
        
        # --- 4. ENGENHARIA DE FEATURES FINAL ---
        
        # Cria Taxa de Dólar
        master_df['Taxa_Dolar'] = master_df['Preco_R'] / master_df['Preco_US']
        
        # Cria "Lag" (Preço do mês anterior)
        # Esta é uma das features mais importantes para previsão de série temporal
        master_df['Preco_R_Lag1'] = master_df['Preco_R'].shift(1)
        
        # Remove linhas com NaN (especialmente o primeiro mês, por causa do Lag)
        master_df_final = master_df.dropna()
        
        print("\n--- DataFrame Mestre (Mensal) Criado com Sucesso ---")
        print(master_df_final.head())
        print(f"\nShape final dos dados: {master_df_final.shape}")

        
        # --- 5. SALVAR E PLOTAR ---
        
        # Salva o DataFrame mestre. É este arquivo que usaremos para a previsão.
        master_df_final.to_csv('master_dataframe_mensal.csv')
        print("\nDataFrame Mestre salvo em 'master_dataframe_mensal.csv'")
        
        # Plota a correlação final
        plotar_correlacao_master(master_df_final)
        
        print("\n--- Preparação de Dados Concluída ---")
        print("Próximo passo: Usar 'master_dataframe_mensal.csv' para treinar um modelo de previsão.")
