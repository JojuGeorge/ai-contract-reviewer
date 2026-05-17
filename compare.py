from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# vector db
db = Chroma(
    collection_name="pdf_collection",
    embedding_function=embedder,
    persist_directory="./chroma_db"
)

loader = PyPDFLoader('./data/uploads/it_services_agreement.pdf')
docs = loader.load()

# combine text
query_text = "\n".join([d.page_content for d in docs])

# semantic search
results = db.similarity_search_with_score(
    query_text,
    k=5
)

for doc, score in results:

    print("=" * 50)
    print("SIMILARITY SCORE:", score)
    print("SOURCE:", doc.metadata.get("source_file"))
    print(doc.page_content[:500])

