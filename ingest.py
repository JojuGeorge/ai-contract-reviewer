from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()


embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# vector db
db = Chroma(
    collection_name="pdf_collection",
    embedding_function=embedder,
    persist_directory="./chroma_db"
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

pdf_folder='./data/contracts'

for file in os.listdir(pdf_folder):
    if file.endswith('.pdf'):
        path = os.path.join(pdf_folder, file)
        
        loader = PyPDFLoader(path)
        docs = loader.load()
        
        chunks = splitter.split_documents(docs)
        
        # metadata
        for chunk in chunks:
            chunk.metadata['source_file'] = file
            
        db.add_documents(chunks)
        print("Indexed: {file}")

        
print("Done")