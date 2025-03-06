import os

# from langchain.vectorstores import FAISS              # deprecated
# from langchain.embeddings import OpenAIEmbeddings     # deprecated
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings

def load_vector_store(*, path: str):
    ## OpenAI
    # embeddings = OpenAIEmbeddings()

    ## Azure OpenAI
    # embeddings = OpenAIEmbeddings(deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT"))
    # embeddings = AzureOpenAIEmbeddings(deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT"))
    # embeddings = AzureOpenAIEmbeddings(azure_endpoint=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT"))
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