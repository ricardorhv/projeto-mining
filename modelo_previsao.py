import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

def carregar_dados_mestre(filepath='master_dataframe_mensal.csv'):
    """
    Carrega o DataFrame mestre salvo anteriormente.
    """
    try:
        df = pd.read_csv(filepath)
        # Converte a coluna 'Data' de volta para datetime e a define como índice
        df['Data'] = pd.to_datetime(df['Data'])
        df.set_index('Data', inplace=True)
        print(f"DataFrame Mestre '{filepath}' carregado com sucesso.")
        print(f"Total de {len(df)} meses de dados prontos para modelagem.")
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo mestre '{filepath}' não encontrado.")
        print("Certifique-se de ter executado o script 'preparacao_modelo.py' primeiro.")
        return None

def plotar_previsao_vs_real(y_test, y_pred, data_inicio_teste):
    """
    Plota o preço real (teste) contra o preço previsto pelo modelo.
    """
    plt.figure(figsize=(15, 7))
    plt.plot(y_test.index, y_test, label='Preço Real', color='blue', linewidth=2)
    plt.plot(y_test.index, y_pred, label='Previsão do Modelo', color='red', linestyle='--', linewidth=2)
    plt.title(f'Previsão do Modelo vs. Preço Real (Dados de Teste a partir de {data_inicio_teste})', fontsize=16)
    plt.xlabel('Data', fontsize=12)
    plt.ylabel('Preço (R$)', fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('grafico_previsao_vs_real.png')
    print("Gráfico de Previsão vs. Real salvo em: 'grafico_previsao_vs_real.png'")

def plotar_importancia_features(model, features_list):
    """
    Plota a importância de cada feature segundo o modelo Random Forest.
    """
    # Cria um DataFrame de importância
    importances = pd.Series(model.feature_importances_, index=features_list)
    importances_sorted = importances.sort_values(ascending=False)
    
    plt.figure(figsize=(10, 8))
    sns.barplot(x=importances_sorted.values, y=importances_sorted.index, palette='viridis')
    plt.title('Importância das Features para Prever o Preço do Milho', fontsize=16)
    plt.xlabel('Nível de Importância', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.tight_layout()
    plt.savefig('grafico_importancia_features.png')
    print("Gráfico de Importância das Features salvo em: 'grafico_importancia_features.png'")

# --- Execução Principal (Modelagem) ---

if __name__ == "__main__":
    sns.set_theme(style="whitegrid")
    
    # 1. Carregar os dados
    df_master = carregar_dados_mestre('master_dataframe_mensal.csv')

    if df_master is not None:
        
        # 2. Definir Features (X) e Alvo (y)
        
        # Nosso alvo (o que queremos prever)
        y = df_master['Preco_R']
        
        # Nossas features (o que usamos para prever)
        # Vamos usar tudo, exceto o próprio Preco_R
        features = df_master.drop(columns=['Preco_R'])
        
        # Guarda a lista de nomes para o gráfico
        features_list = features.columns.tolist()
        
        X = features
        
        print("\n--- Configuração do Modelo ---")
        print(f"Alvo (y): Preco_R")
        print(f"Features (X): {', '.join(features_list)}")
        
        
        # 3. Dividir em Treino e Teste (CRONOLOGICAMENTE)
        # Para séries temporais, NUNCA podemos embaralhar os dados.
        # Vamos usar 80% dos dados para treinar e 20% para testar.
        
        split_percent = 0.8
        split_point = int(len(X) * split_percent)
        
        X_train = X.iloc[:split_point]
        y_train = y.iloc[:split_point]
        
        X_test = X.iloc[split_point:]
        y_test = y.iloc[split_point:]
        
        data_inicio_treino = X_train.index.min().strftime('%Y-%m')
        data_fim_treino = X_train.index.max().strftime('%Y-%m')
        data_inicio_teste = X_test.index.min().strftime('%Y-%m')
        data_fim_teste = X_test.index.max().strftime('%Y-%m')
        
        print(f"\nDados de Treino: {data_inicio_treino} a {data_fim_treino} ({len(X_train)} meses)")
        print(f"Dados de Teste:  {data_inicio_teste} a {data_fim_teste} ({len(X_test)} meses)")
        
        
        # 4. Treinar o Modelo
        print("\nTreinando o modelo RandomForestRegressor...")
        
        # n_estimators = número de "árvores" na floresta
        # max_depth = profundidade de cada árvore (ajuda a evitar overfitting)
        # random_state = para resultados reproduzíveis
        model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=10, 
            random_state=42, 
            n_jobs=-1, # Usa todos os processadores
            min_samples_leaf=2 # Exige pelo menos 2 amostras em uma "folha"
        )
        
        model.fit(X_train, y_train)
        print("Modelo treinado com sucesso!")
        
        
        # 5. Fazer Previsões e Avaliar
        y_pred = model.predict(X_test)
        
        # Calcular Métricas
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print("\n--- Resultados da Avaliação (Dados de Teste) ---")
        print(f"R² (R-quadrado): {r2:.4f}")
        print(f"Erro Médio Absoluto (MAE): R$ {mae:.2f}")
        
        print("\nInterpretação:")
        print(f"R-quadrado (R²): Nosso modelo consegue explicar {r2*100:.2f}% da variação do preço do milho.")
        print(f"Erro Médio (MAE): Em média, as previsões do modelo erraram o preço em R$ {mae:.2f}.")
        
        
        # 6. Visualizar Resultados
        print("\nGerando gráficos de resultados...")
        
        # Gráfico 1: Previsão vs. Real
        plotar_previsao_vs_real(y_test, y_pred, data_inicio_teste)
        
        # Gráfico 2: Importância das Features
        plotar_importancia_features(model, features_list)
        
        print("\n--- Modelagem Concluída ---")
        print("Próximo passo: Analisar os gráficos e, se estiver satisfeito, construir o Dashboard.")
