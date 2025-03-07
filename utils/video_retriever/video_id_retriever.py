from typing import List, Tuple, Any
import os
import asyncio

from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class VideoIDRetriever():
    """ Retrieve Youtube Video ID from a vector DB."""
    def __init__(self, llm: AzureChatOpenAI, vectorDBPath: str):
        """  
        Initializes VideoIDRetriever class.

        :param llm: LLM instance, either OpenAI or AzureOpenAI.
        :param vectorDBPath: Local VectorDB path to be loaded.
        """
        self.llm = llm
        self.vectorDBPath: str = vectorDBPath
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.environ.get("AZURE_EMBEDDINGS_DEPLOYMENT")
        )
        self.vectorStore = self._load_vector_store()

    def _load_vector_store(self) -> FAISS:
        """
        Loads the vector store from the specified path.

        This method initializes the vector store with the embeddings from AzureOpenAI and sets it up for document retrieval.

        :return: A FAISS vector store object initialized with embeddings.
        """
        vectorStore = FAISS.load_local(
            folder_path=self.vectorDBPath, 
            embeddings=self.embeddings, 
            allow_dangerous_deserialization=True
        )
        # vectorStore.docstore._dict # show DB data separated by chunks & indexes.

        return vectorStore
    
    async def _aload_vector_store(self) -> FAISS:
        """
        Asynchronously loads the vector store.

        This method is an asynchronous wrapper around `_load_vector_store` to facilitate non-blocking I/O operations.

        :return: A FAISS vector store object initialized with embeddings.
        """
        return await asyncio.to_thread(self._load_vector_store)

    def _retrieve_docs(self, query: str, k: int=2) -> List[Tuple[Any, float]]:
        """
        Retrieves documents from vector store based on user input, makes semantich search with score.

        :param query: The query string for which similar documents are to be retrieved.
        :param k: The number of documents to retrieve.
        :return: A list of tuples containing the document and its similarity score.
        """
        retriever = self.vectorStore.similarity_search_with_score(
            query=query, 
            k=k
        )
        # print(f"\ndocs retrieved: \n{retriever}\n")

        return retriever
    
    async def _aretrieve_docs(self, query: str, k: int=2) -> List[Tuple[Any, float]]:
        """
        Asynchronously retrieves documents from vector store based on user input, makes semantich search with score.

        This method is an asynchronous wrapper around `_retrieve_docs` to facilitate non-blocking I/O operations.

        :param query: The query string for which similar documents are to be retrieved.
        :param k: The number of documents to retrieve.
        :return: A list of tuples containing the document and its similarity score.
        """
        return await asyncio.to_thread(self._retrieve_docs, query, k)
    
    def _format_system_message(self, retriever: List[Tuple[Any, float]]) -> str:
        """
        Formats a system message to be sent to the language model based on the retrieved documents.

        :param retriever: The retrieved documents from the vector store.
        :return: A formatted string containing instructions and the retrieved documents for the language model.
        """
        system_message: str = """"\
            Your job is to answer the question with the YoutubeID based only on the following context: \
            %s
            
            The YoutubeID is the one at the beginning of each document context, the combination of characters before the ':' \
            If the context answers the question, return the `ID` only, if not, return `None`.

            Example:
            If the context contains the answer: KJN874NF
            If the context doesn't answer: None

            Now your turn:
            Question:
        """ %(retriever)

        return system_message
    
    def get_video_id(self, userInput: str) -> str:
        """
        Retrieves the YouTube video ID based on the user input.

        This method processes the user input, retrieves relevant documents, and formats a message to get a response from the language model.

        :param userInput: The user input string based on which the YouTube video ID is to be retrieved.
        :return: The YouTube video ID as a string.
        """
        retriever = self._retrieve_docs(query=userInput)
        system_message = self._format_system_message(retriever)

        messages = [
            ("system", system_message),
            ("human", userInput),
        ]

        botOutput = self.llm.invoke(messages)

        return botOutput.content

    async def aget_video_id(self, userInput: str) -> str:
        """
        Asynchronously retrieves the YouTube video ID based on the user input.

        This method is an asynchronous version of `get_video_id`, designed to facilitate non-blocking I/O operations.

        :param userInput: The user input string based on which the YouTube video ID is to be retrieved.
        :return: The YouTube video ID as a string.
        """
        retriever = await self._aretrieve_docs(query=userInput)
        system_message = self._format_system_message(retriever)

        messages = [
            ("system", system_message),
            ("human", userInput),
        ]

        botOutput = await asyncio.to_thread(self.llm.invoke, messages)

        return botOutput.content
