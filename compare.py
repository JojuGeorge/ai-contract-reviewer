# from langchain_chroma import Chroma
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_openai import OpenAIEmbeddings
# from dotenv import load_dotenv

# load_dotenv()

# embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# # vector db
# db = Chroma(
#     collection_name="pdf_collection",
#     embedding_function=embedder,
#     persist_directory="./chroma_db"
# )

# loader = PyPDFLoader('./data/uploads/it_services_agreement.pdf')
# docs = loader.load()

# # combine text
# query_text = "\n".join([d.page_content for d in docs])

# # semantic search
# results = db.similarity_search_with_score(
#     query_text,
#     k=5
# )

# for doc, score in results:

#     print("=" * 50)
#     print("SIMILARITY SCORE:", score)
#     print("SOURCE:", doc.metadata.get("source_file"))
#     print(doc.page_content[:500])

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from difflib import SequenceMatcher
import difflib
import os

load_dotenv()

embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# vector db
db = Chroma(
    collection_name="pdf_collection",
    embedding_function=embedder,
    persist_directory="./chroma_db"
)

# -----------------------------
# LOAD CONSUMER CONTRACT
# -----------------------------
consumer_pdf = './data/uploads/revised_business_consulting_agreement.pdf'

loader = PyPDFLoader(consumer_pdf)
consumer_docs = loader.load()

consumer_text = "\n".join([d.page_content for d in consumer_docs])

# -----------------------------
# FIND MOST SIMILAR CONTRACT
# -----------------------------
results = db.similarity_search_with_score(
    consumer_text,
    k=1
)

matched_doc, score = results[0]

matched_file = matched_doc.metadata.get("source_file")

print("=" * 60)
print("MATCHED CONTRACT:", matched_file)

# -----------------------------
# LOAD ORIGINAL COMPANY CONTRACT
# -----------------------------
original_path = f'./data/contracts/{matched_file}'

loader2 = PyPDFLoader(original_path)
original_docs = loader2.load()

original_text = "\n".join([d.page_content for d in original_docs])

# -----------------------------
# SIMILARITY %
# -----------------------------
semantic_similarity = max(0, min(100, (1 - score) * 100))

# text similarity
text_similarity = SequenceMatcher(
    None,
    original_text,
    consumer_text
).ratio() * 100

difference_percent = 100 - text_similarity

print(f"Semantic Similarity: {semantic_similarity:.2f}%")
print(f"Text Similarity: {text_similarity:.2f}%")
print(f"Difference: {difference_percent:.2f}%")

# -----------------------------
# SHOW DIFFERENCES
# -----------------------------
print("\n" + "=" * 60)
print("CONTRACT DIFFERENCES")
print("=" * 60)

original_lines = original_text.splitlines()
consumer_lines = consumer_text.splitlines()

diff = difflib.unified_diff(
    original_lines,
    consumer_lines,
    fromfile='Original Contract',
    tofile='Consumer Contract',
    lineterm=''
)

for line in diff:
    print(line)