import requests
from pymongo import MongoClient
from datetime import datetime
from dateutil.parser import parse
import pytz

tz = pytz.timezone('America/Sao_Paulo')


API_KEY = "96b1588fd48c4f278e281cffadeb8644"  
MONGO_URI = "mongodb://root:root@localhost:27017/"  
DB_NAME = "milho_db"
COLLECTION_NAME = "noticias"
QUERY = "preço do milho"  
DATE_START = "2025-08-16"  
DATE_END = "2025-09-16"    
LANGUAGE = "pt"            


def fetch_noticias_newsapi(query, date_start, date_end, api_key, language="pt"):
    noticias = []
    try:
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": date_start,
            "to": date_end,
            "language": language,
            "sortBy": "publishedAt",  
            "apiKey": api_key,
            "pageSize": 100  
        }
        
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        
        articles = data.get("articles", [])
        start_date = datetime.strptime(date_start, "%Y-%m-%d")
        end_date = datetime.strptime(date_end, "%Y-%m-%d")
        
        for article in articles:
            
            title = article.get("title", "Sem título")
            
            
            published_at_str = article.get("publishedAt", "")
            date = parse(published_at_str) if published_at_str else None
            if date:
                date = date.replace(tzinfo=None)  
            if not date or date < start_date or date > end_date:
                continue  
            
            
            content = article.get("description", "Sem conteúdo")
            
            
            source = article.get("source", {}).get("name", "Desconhecida")
            source_url = article.get("url", "")
            
            noticias.append({
                "data": date.strftime("%d/%m/%Y"),
                "titulo": title,
                "conteudo": content,
                "fonte": source,
                "url_fonte": source_url,
                "data_coleta": datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        print(f"Encontradas {len(noticias)} notícias no intervalo de datas.")
        
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição à NewsAPI: {e}")
        if "apiKey" in str(e).lower():
            print("Verifique se a API_KEY está correta e válida.")
    except Exception as e:
        print(f"Erro ao processar notícias: {e}")
    
    return noticias


def save_to_mongodb(noticias):
    try:
        
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        
        collection.create_index([("titulo", 1), ("data", 1)], unique=True)

        
        for noticia in noticias:
            try:
                collection.insert_one(noticia)
                print(f"Notícia '{noticia['titulo'][:50]}...' salva com sucesso.")
            except Exception as e:
                print(f"Notícia '{noticia['titulo'][:50]}...' já existe ou erro: {e}")

        client.close()
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")


if __name__ == "__main__":
    noticias = fetch_noticias_newsapi(QUERY, DATE_START, DATE_END, API_KEY, LANGUAGE)
    if noticias:
        save_to_mongodb(noticias)
    else:
        print("Nenhuma notícia encontrada no intervalo de datas ou erro na API.")