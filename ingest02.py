from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

import os
import json
import uuid

load_dotenv()

# models
embedder = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0
)

# chroma vector db
db = Chroma(
    collection_name="contracts_collection",
    embedding_function=embedder,
    persist_directory="./chroma_db"
)


CONTRACT_FOLDER = "./data/contracts"

# extract caluses using gpt
def extract_clauses(text):

    prompt = f"""
You are a legal contract parser.

Extract all legal clauses from this contract.

Return valid JSON array only.

Format:
[
  {{
    "title": "clause title",
    "content": "full clause text"
  }}
]

CONTRACT:
{text}
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    try:
        clauses = json.loads(content)
        return clauses

    except Exception as e:
        print("Clause extraction failed")
        print(e)
        return []



# ingest contract for embedding and saving to db
for file in os.listdir(CONTRACT_FOLDER):
    if not file.endswith(".pdf"):
        continue

    path = os.path.join(CONTRACT_FOLDER, file)
    print(f"\nProcessing: {file}")

    loader = PyPDFLoader(path)
    docs = loader.load()    # extract text from pdf, list of pages(text extracted)

    full_text = "\n".join(
        [doc.page_content for doc in docs]
    )

    # get extracted clauses from the gpt. good for diff types of extracted data
    clauses = extract_clauses(full_text)

    texts = []
    metadatas = []
    ids = []

    for index, clause in enumerate(clauses):
        texts.append(clause["content"])
        metadatas.append({
            "source_file": file,
            "source_path": path,
            "clause_number": index + 1,
            "clause_title": clause["title"]
        })
        ids.append(str(uuid.uuid4()))


    # add text to chroma db after embedding then stores in the vector db
    db.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Indexed {len(clauses)} clauses")

print("\nDONE")