from google import genai
from settings import cases_urls
from parse import Parser
from fake_useragent import UserAgent
from chromadb import PersistentClient
from chromadb import QueryResult
import uuid


class EoraAssistant:

    def __init__(self,
                 genai_client: genai.Client, 
                 parser: Parser,
                 chroma_client: PersistentClient):

        self.genai_client = genai_client
        self.parser = parser
        
        chroma_client = chroma_client
        self.collection = chroma_client.get_or_create_collection(
            name="company_cases",
            metadata={"description": "Примеры проектов и их эмбеддинги"}
        )

    def _create_chunks(self, paragraphs: list[str], max_chunk_size: int = 1000) -> list[str]:

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 1 <= max_chunk_size:
                current_chunk += f' {paragraph}'
            else:
                chunks.append(current_chunk)
                current_chunk = paragraph
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _get_embedding(self, chunk: str) -> list[float]:

        result = self.genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=chunk
        )
        if not result or not getattr(result, "embeddings", None):
            raise ValueError("Ошибка во время создания эмбеддинга")
        return result.embeddings[0].values


    def _final_query_creation(self, results: QueryResult, query: str):

        context_chunks = results.get("documents", [[]])[0]
        metadatas_list = results.get('metadatas', [[]])[0]

        if not context_chunks:
            return "К сожалению, в моей базе знаний нет информации по вашему вопросу. Пожалуйста, посетите сайт компании."

        source_urls = [meta['source_url'] for meta in metadatas_list]
        unique_urls = list(set(source_urls))
        
        context_urls_str = "\n".join(unique_urls)
        context_text = "\n\n".join(context_chunks)

        final_query = f"""Ты — эксперт компании EORA. 
        Отвечай на основании предоставленных данных + добавь в конце ссылки на источники в таком формате [1], [2] и тд. 
        Если не сможешь ответить, так и скажи.
        Контекст:\n{context_text}\n\nСсылки на источники:\n{context_urls_str}\n\nВопрос:\n{query}"""

        return final_query

    def add_documents_from_urls(self, urls: list[str], batch_size: 100):

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        
        for url_index, url in enumerate(urls):
            try:

                paragraphs = self.parser.get_main_info_list(url)
                chunks = self._create_chunks(paragraphs)
                
                for chunk_index, chunk in enumerate(chunks):
                    if not chunk:
                        continue
                    
                    embeddings.append(self._get_embedding(chunk))
                    ids.append(f"url_{url_index}_chunk_{chunk_index}_{str(uuid.uuid4())}")
                    metadatas.append({"source_url": url, "chunk_index": chunk_index})
                    documents.append(chunk)

                    if len(ids) >= batch_size:
                        self.collection.add(
                            ids=ids,
                            embeddings=embeddings,
                            documents=documents,
                            metadatas=metadatas
                        )
                        ids = []
                        embeddings = []
                        metadatas = []
                        documents = []

            except Exception as e:
                print(f"Ошибка при обработке URL {url}: {e}")

        
        if ids:
            self.collection.add(
                            ids=ids,
                            embeddings=embeddings,
                            documents=documents,
                            metadatas=metadatas
                        )

        

    def get_answer(self, query: str, n_results: int = 7) -> str:

        query_embedding = self._get_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas"]
        )

        final_query = self._final_query_creation(results=results, query=query)

        response = self.genai_client.models.generate_content(
            model='gemma-3n-e4b-it',
            contents=final_query
        )
        
        return response.text