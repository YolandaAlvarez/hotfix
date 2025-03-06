import os
import json

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from PyPDF2 import PdfReader

from utils.constants import SOURCE_DISHWASHER_USER_MANUAL, SOURCE_DISHWASHER_ERROR_HANDLING

def get_pdf_text(*, pdf):
    text = ""

    pdf_reader = PdfReader(pdf)

    for page in pdf_reader.pages:
        text += page.extract_text()

    return text

def get_text_chunks(*, text):
    textSplitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=500,  # characters
        chunk_overlap=50,  # characters tolerance
        length_function=len,
    )
    chunks = textSplitter.split_text(text)

    return chunks

def create_vector_store(*, text_chunks, filename):
    ## OpenAI
    # embeddings = OpenAIEmbeddings()

    ## Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
    )

    vectorStore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vectorStore.save_local(filename)

    return vectorStore

def merge_vector_store(*, text_chunks, filename):
    ## OpenAI
    # embeddings = OpenAIEmbeddings()

    ## Azure OpenAI
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
    )

    newVectorStore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vectorStore = FAISS.load_local(filename, embeddings, allow_dangerous_deserialization=True)

    vectorStore.merge_from(newVectorStore)
    vectorStore.save_local(filename)

    return vectorStore

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

    pdf1 = SOURCE_DISHWASHER_USER_MANUAL
    pdf2 = SOURCE_DISHWASHER_ERROR_HANDLING
    vectorDBFilename: str = './newDB'

    ## 2 PDF's script
    i: int = 1
    for pdf in (pdf1, pdf2):
        print(f"Starting pdf: {i} process.")
        
        rawText = get_pdf_text(pdf=pdf)
        textChunks = get_text_chunks(text=rawText)

        if os.path.exists(path=vectorDBFilename):
            vectorStore = merge_vector_store(text_chunks=textChunks, filename=vectorDBFilename)
        else:
            vectorStore = create_vector_store(text_chunks=textChunks, filename=vectorDBFilename)
        
        i += 1
        print(f"Finishing pdf: {i} process.\n")


    # ## Single PDF Script
    # rawText = get_pdf_text(pdf=pdf2)
    # print('\033[91m' + "rawText: \n" + '\033[93m' + rawText + '\033[0m' + "\n\n")

    # textChunks = get_text_chunks(text=rawText)
    # print('\033[91m' + "textChunks: \n" + '\033[95m', textChunks, '\033[0m' + "\n\n")

    # if os.path.exists(path=vectorDBFilename):
    #     vectorStore = merge_vector_store(text_chunks=textChunks, filename=vectorDBFilename)
    # else:
    #     vectorStore = create_vector_store(text_chunks=textChunks, filename=vectorDBFilename)
    

if __name__ == '__main__':
    main()