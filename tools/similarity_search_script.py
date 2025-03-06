import os
import json

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from utils.constants import DB_DISHWASHER

def load_vector_store(*, path: str):
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
    )
    
    vectorStore = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    # vectorStore.docstore._dict # show DB data separated by chunks & indexes.

    return vectorStore

def retrieval_db(vectorStore, query: str):
    """ Check if Similarity Search is working properly """
    docs = vectorStore.similarity_search(query)
    print(f"\ndocs: \t{docs}")

    return docs
# load_dotenv()

def main():
    load_dotenv()
    vectorDB = load_vector_store(path=DB_DISHWASHER)

    query = input("Query: ")
    kDocs = int(input("k docs to retrieve, recommendation is 3: "))

    docs = vectorDB.similarity_search_with_score(query=query, k=kDocs)

    print("\n", docs)


if __name__ == '__main__':
    main()