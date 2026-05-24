from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

import numpy as np
import os
import json

load_dotenv()

# embedding model
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0
)

# chroma vector db
db = Chroma(
    collection_name="contracts_collection",
    embedding_function=embedding_model,
    persist_directory="./chroma_db"
)

# clause extraction using gpt


def extract_clauses(text):
    prompt = f"""
You are a legal contract parser.
Extract all legal clauses.
Return JSON only.

Format:
[
  {{
    "title": "clause title",
    "content": "complete clause text"
  }}
]
CONTRACT:
{text}
"""
    response = llm.invoke(prompt)
    return json.loads(response.content)

# find distance in vector using the cosine similarity method


def embedding_similarity(text1, text2):

    emb1 = embedding_model.embed_query(text1)
    emb2 = embedding_model.embed_query(text2)

    score = cosine_similarity(
        [emb1],
        [emb2]
    )[0][0]

    return score


# get customer revised contracts
UPLOAD_FOLDER = "./data/uploads"

for file in os.listdir(UPLOAD_FOLDER):
    if not file.endswith(".pdf"):
        continue

    print("\n\n\n" + "=" * 80)
    print("CHECKING:", file)
    print("=" * 80)

    customer_path = os.path.join(
        UPLOAD_FOLDER,
        file
    )

    loader = PyPDFLoader(customer_path)
    docs = loader.load()

    customer_text = "\n".join(
        [d.page_content for d in docs]
    )

    # find most similar contract
    # semantic contract search in the vec db and return the text
    results = db.similarity_search_with_score(
        customer_text,
        k=10
    )

    best_doc, score = results[0]

    company_contract = best_doc.metadata["source_file"]

    print(f"\nMatched Contract: {company_contract}")

    # load most similar company contract
    original_path = (
        f"./data/contracts/{company_contract}"
    )

    loader2 = PyPDFLoader(original_path)
    docs2 = loader2.load()

    original_text = "\n".join(
        [d.page_content for d in docs2]
    )

    # clause extraction using gpt for both
    original_clauses = extract_clauses(
        original_text
    )

    customer_clauses = extract_clauses(
        customer_text
    )

    # classification of clauses
    modified = []
    added = []
    removed = []

    matched_indexes = set()

    # clause comparison
    for customer_clause in customer_clauses:

        best_score = 0
        best_match = None

        for idx, original_clause in enumerate(
            original_clauses
        ):
            score = embedding_similarity(
                customer_clause["content"],
                original_clause["content"]
            )

            if score > best_score:
                best_score = score
                best_match = idx

        # classify to matched, modified, added clauses
        if best_score >= 0.98:
            matched_indexes.add(best_match)
        elif best_score >= 0.75:
            modified.append({
                "similarity": round(
                    best_score * 100,
                    2
                ),
                "original": original_clauses[
                    best_match
                ],
                "customer": customer_clause
            })
            matched_indexes.add(best_match)

        else:
            added.append({
                "clause": customer_clause
            })

    # removed clauses
    for idx, clause in enumerate(original_clauses):
        if idx not in matched_indexes:
            removed.append({
                "clause": clause
            })

    # overall similarity
    overall_similarity = (
        embedding_similarity(
            original_text,
            customer_text
        ) * 100
    )

    difference = 100 - overall_similarity

    # AI legal summary prompt
    summary_prompt = f"""
You are a senior legal contract reviewer.

Compare these contracts and generate:

1. Executive summary
2. Critical legal risks
3. Financial risks
4. Liability changes
5. Termination changes
6. Compliance risks
7. Final recommendation

ORIGINAL:
{original_text}

REVISED:
{customer_text}
"""

    summary = llm.invoke(summary_prompt)

    # output
    print("\n\n" + "=" * 80)
    print("FINAL ANALYSIS")
    print("=" * 80)

    print(
        f"Similarity: {overall_similarity:.2f}%"
    )
    print(
        f"Difference: {difference:.2f}%"
    )

    print("\n\nMODIFIED CLAUSES")
    print("-" * 80)

    for item in modified:
        print(
            f"Clause: "
            f"{item['customer']['title']}"
        )
        print(
            f"Similarity: {item['similarity']}%\n"
        )

    print("\n\nADDED CLAUSES")
    print("-" * 80)

    for item in added:
        print(
            item["clause"]["title"]
        )

    print("\n\nREMOVED CLAUSES")
    print("-" * 80)

    for item in removed:
        print(
            item["clause"]["title"]
        )

    print("\n\nAI LEGAL SUMMARY")
    print("-" * 80)

    print(summary.content)
