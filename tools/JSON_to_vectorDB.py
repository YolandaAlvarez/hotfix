"""
Script to save JSON file data to a VectorDB, each key: value will be a 'Document' to be stored.
"""

import json
from uuid import uuid4
import os
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

def create_vector_store(*, text_chunks, filename: str, uuids) -> FAISS:
    ## OpenAI
    # embeddings = OpenAIEmbeddings()

    ## Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
    )
    

    # vectorStore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vectorStore = FAISS.from_documents(
        documents=text_chunks, 
        embedding=embeddings,
        ids=uuids
    )
    vectorStore.save_local(filename)

    return vectorStore

def load_vector_store(*, path: str) -> FAISS:
    ## OpenAI
    # embeddings = OpenAIEmbeddings()

    ## Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
    )
    
    vector_store = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    # vector_store.docstore._dict # show DB data separated by chunks & indexes.

    return vector_store

def create_embeddings() -> list:
    with open("docs/transcriptions_with_empty_keys.json", 'r') as file:
        data = json.load(file)

    documents: list = []

    for i, (key, value) in enumerate(data.items()):
        print(f'{i} | {key}a: {value}')

        i = Document(
            page_content=f"{key}: {value}",
            metadata={"source": "YouTubeID"}
        )

        documents.append(i)

    return documents

def main():
    documents = create_embeddings()
    print("\n\n\n\n")
    print(documents)
    
    uuids = [str(uuid4()) for _ in range(len(documents))]
    print("\n\n", uuids)

    vectorStore = create_vector_store(
        text_chunks=documents, 
        filename='./db/transcriptions_new', 
        uuids=uuids
        )

if __name__ == '__main__':
    main()








""" 


for key, value in data.items():
    print(f"{key}: {value}")



document_1 = Document(
    page_content='I had chocalate chip pancakes and scrambled eggs for breakfast this morning.',
    metadata={'source': 'tweet'},
)

document_2 = Document(
    page_content='The weather forecast for tomorrow is cloudy and overcast, with a high of 62 degrees.',
    metadata={'source': 'news'},
)

document_3 = Document(
    page_content='Building an exciting new project with LangChain - come check it out!',
    metadata={'source': 'tweet'},
)

document_4 = Document(
    page_content='Robbers broke into the city bank and stole $1 million in cash.',
    metadata={'source': 'news'},
)

document_5 = Document(
    page_content='Wow! That was an amazing movie. I can't wait to see it again.',
    metadata={'source': 'tweet'},
)

document_6 = Document(
    page_content='Is the new iPhone worth the price? Read this review to find out.',
    metadata={'source': 'website'},
)

document_7 = Document(
    page_content='The top 10 soccer players in the world right now.',
    metadata={'source': 'website'},
)

document_8 = Document(
    page_content='LangGraph is the best framework for building stateful, agentic applications!',
    metadata={'source': 'tweet'},
)

document_9 = Document(
    page_content='The stock market is down 500 points today due to fears of a recession.',
    metadata={'source': 'news'},
)

document_10 = Document(
    page_content='I have a bad feeling I am going to get deleted :(',
    metadata={'source': 'tweet'},
)

documents = [
    document_1,
    document_2,
    document_3,
    document_4,
    document_5,
    document_6,
    document_7,
    document_8,
    document_9,
    document_10,
]
uuids = [str(uuid4()) for _ in range(len(documents))]

vector_store.add_documents(documents=documents, ids=uuids)
"""