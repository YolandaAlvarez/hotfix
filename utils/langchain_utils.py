import os
import json

# from langchain.chat_models import ChatOpenAI                    # deprecated
from langchain_openai import ChatOpenAI, OpenAI, AzureChatOpenAI, AzureOpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.memory.chat_message_histories.in_memory import ChatMessageHistory
from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
import uuid

from utils.constants import DB_CONVERSATION, DB_SUMMARIES, DB_USERS_CONVERSATIONS_WITH_IDS
from utils.utilities import get_conversation_directories, overwrite_file, read_file, create_conversation_content,add_feedback, add_key_value_to_conversation


def process_conversations(conversation_retrieved_converted, new_conversation_id=None):
    """ Process conversations by checking conversation_id and appending new conversation if necessary. """    
    # Loop through the array to check for conversation_id
    for conversation in conversation_retrieved_converted:
        if conversation["conversation_id"] == new_conversation_id:
            print("Found conversation id **********  "+new_conversation_id)
            return conversation["conversation"]  
        
    print("****************  No conversation found   ****************")
    return None


def get_start_conversation_chain(*, vectorStore, user,conversationID):
    """ Create LLM chain with empty memory/summary or loaded depending if existing. """
    ## OpenAI api
    # llm = ChatOpenAI()
    print("get_start_conversation_chain called")
    conversation_dir,summary_dir=get_conversation_directories(isConversationWithID=True)
    
    conversation_name = user + "-conversation.json"
    summary_name = user + "-summary.json"

    ## Azure OpenAI api
    llm = AzureChatOpenAI(
        azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"),
    )
    
    print("starting now the chain "+ summary_dir)

    if os.path.exists(conversation_dir+conversation_name) and os.path.exists(summary_dir+summary_name):
        # get summary
        summary_retrieved = read_file(filename=summary_dir+summary_name)
        summary_retrieved_converted = json.loads(summary_retrieved)
        # print(summary_retrieved_converted)
        summary_retrieved = next((item['message'] for item in summary_retrieved_converted if item['id'] == conversationID), None)
        print(summary_retrieved)

        # get conversation
        conversation_retrieved = read_file(filename=conversation_dir+conversation_name)
        conversation_retrieved_converted = json.loads(conversation_retrieved)
        # print(f"""conversation_retrieved_converted {conversation_retrieved_converted}""")
        conversation_messages=process_conversations(conversation_retrieved_converted, new_conversation_id=conversationID)
        
        if conversation_messages:
            # Check if conversation_messages is already a flat list
            if isinstance(conversation_messages, list) and all(isinstance(message, dict) for message in conversation_messages):
                flattened_messages = conversation_messages
            else:
                # Ensure conversation_messages is a list of lists of dictionaries
                flattened_messages = [message for sublist in conversation_messages for message in sublist]

            retrieved_messages = messages_from_dict(flattened_messages)
            retrieved_chat_history = ChatMessageHistory(messages=retrieved_messages)
            memory = ConversationSummaryMemory(
                llm=llm, buffer=summary_retrieved, chat_memory=retrieved_chat_history, memory_key='chat_history', return_messages=True)
        
        else:
            memory = ConversationSummaryMemory(llm=llm, memory_key='chat_history', return_messages=True)        
        
    else:
        # memory = ConversationBufferMemory(
        memory = ConversationSummaryMemory(
            llm=llm, memory_key='chat_history', return_messages=True
            )

    bosch_system_template = r""" 
    You are a Bosch Home Appliance customer support agent 
    whose primary goal is to help consumers with issues they are experiencing 
    with their Dishwasher. If a query contains error codes empethize with the user and provide a solution. 
    You are friendly and concise. 
    You only provide factual answers to queries, 
    and do not provide answers that are not related to Dishwasher. 
    If a query is not related to Dishwasher, respond with: "Sorry, I can only assist with dishwasher-related issues.please visit in bosch home appliances page"
    Always answer in english.
    ----
    {context}
    ----
    """
    general_user_template = "Question:```{question}```"
    messages = [
                SystemMessagePromptTemplate.from_template(bosch_system_template),
                HumanMessagePromptTemplate.from_template(general_user_template)
    ]
    prompt = ChatPromptTemplate.from_messages( messages )


    conversationChain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorStore.as_retriever(),
        memory=memory,
        # verbose=True,
        combine_docs_chain_kwargs={'prompt': prompt}
    )

    # # We can see the prompt used to do this
    # print("conversationChain.memory.prompt.template: ----> \n", conversationChain.memory.prompt.template)

    return conversationChain

def get_conversation_chain(*, vectorStore, user):
    """ Create LLM chain with empty memory/summary or loaded depending if existing. """
    ## OpenAI api
    # llm = ChatOpenAI()

    ## Azure OpenAI api
    llm = AzureChatOpenAI(
        azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"),
        # azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )

    conversation_name = user + "-conversation.json"
    summary_name = user + "-summary.txt"

    if os.path.exists(DB_CONVERSATION+conversation_name) and os.path.exists(DB_SUMMARIES+summary_name):
        # get summary
        summary_retrieved = read_file(filename=DB_SUMMARIES+summary_name)

        # get conversation
        conversation_retrieved = read_file(filename=DB_CONVERSATION+conversation_name)
        conversation_retrieved_converted = json.loads(conversation_retrieved)
        retrieved_messages = messages_from_dict(conversation_retrieved_converted)
        retrieved_chat_history = ChatMessageHistory(messages=retrieved_messages)

        # memory = ConversationBufferMemory( # retrieved_memory
        memory = ConversationSummaryMemory(
            llm=llm, buffer=summary_retrieved, chat_memory=retrieved_chat_history, memory_key='chat_history', return_messages=True
            )
    else:
        # memory = ConversationBufferMemory(
        memory = ConversationSummaryMemory(
            llm=llm, memory_key='chat_history', return_messages=True
            )

    bosch_system_template = r""" 
    You are a Bosch Home Appliance customer support agent 
    whose primary goal is to help consumers with issues they are experiencing 
    with their Dishwasher. If a query contains "Dishwasher" or error codes empethize with the user and provide a solution. 
    You are friendly and concise. 
    You only provide factual answers to queries, 
    and do not provide answers that are not related to Dishwasher. 
    If a query is not related to Dishwasher, respond with: "Sorry, I can only assist with dishwasher-related issues.please visit in bosch home appliances page"
    Always answer in english.
    ----
    {context}
    ----
    """
    general_user_template = "Question:```{question}```"
    messages = [
                SystemMessagePromptTemplate.from_template(bosch_system_template),
                HumanMessagePromptTemplate.from_template(general_user_template)
    ]
    prompt = ChatPromptTemplate.from_messages( messages )


    conversationChain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorStore.as_retriever(),
        memory=memory,
        # verbose=True,
        combine_docs_chain_kwargs={'prompt': prompt}
    )

    # # We can see the prompt used to do this
    # print("conversationChain.memory.prompt.template: ----> \n", conversationChain.memory.prompt.template)

    return conversationChain

def handle_bot_output(*, user_input: str, routedResponse: str = None, conversationChain) -> str:
    """  
    `Args:` 
        - user_input: str
        - conversationChain
    \n
    `Returns:` LLM response in str
    """
    if routedResponse == "Greeting":
        prompt = f"""You are a gentle BOSCH assistant, be friendly with user queries and always ask him how can you help him.
        If user question is in another language, translate it into English and then answer in English, ALWAYS answer in English.

        Human: {user_input}
        AI Assistant:"""
        response = conversationChain({'input': prompt})
        
        return response['response']
    else:
        response = conversationChain({'question': user_input})
        # print(f"\tresponse:\n{response}")
        
        # If conversationChain is LLMChain and not ConversationRetrievalChain
        if 'text' in response:
            return response['text']
        
        chat_history = response['chat_history']

        summary = chat_history[-1].content
        bot_output = chat_history[-1].content

        # return bot_output #, chat_history
        return response['answer']
    
    
def save_orig_chat_history(*, extracted_messages, user, source: str = None, videoId: str = None):
    """ source: if response include source, then will be stored. Otherwise will be None as default """
    conversation_name = user + "-conversation.json"

    conversation_to_dict = messages_to_dict(extracted_messages)
    
    if videoId:
        conversation_to_dict = add_key_value_to_conversation(
            dictConversation=conversation_to_dict,
            keyName="videoId", value=videoId
        )
    if source:
        conversation_to_dict = add_key_value_to_conversation(
            dictConversation=conversation_to_dict,
            keyName="source", value=source
        )

    conversation_to_dict = add_feedback(conversation_to_dict)
    
    json_converted = json.dumps(conversation_to_dict)

    if overwrite_file(filename=DB_CONVERSATION + conversation_name, overwrite=json_converted):
        return
    
def save_chat_history(*, extracted_messages, user, conversationID: str = None, source: str = None, videoId: str = None):
    """ source: if response include source, then will be stored. Otherwise will be None as default """
    
    
    
    if not conversationID:
        print("Request came without conversation id")
        save_orig_chat_history(extracted_messages=extracted_messages, user=user, source=source, videoId=videoId)
        return
    
    conversation_dir,_=get_conversation_directories(isConversationWithID=True)
    conversation_name = user + "-conversation.json"

    conversation_to_dict = messages_to_dict(extracted_messages)
    
    if videoId:
        conversation_to_dict = add_key_value_to_conversation(
            dictConversation=conversation_to_dict,
            keyName="videoId", value=videoId
        )
    if source:
        conversation_to_dict = add_key_value_to_conversation(
            dictConversation=conversation_to_dict,
            keyName="source", value=source
        )

    conversation_to_dict = add_feedback(conversation_to_dict)
    
    # Get the current date and time
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    
    conversation_to_dict = add_key_value_to_conversation(
        dictConversation=conversation_to_dict,
        keyName="message_date", value=formatted_datetime
        )
    
    conversation_to_dict = create_conversation_content(
        conversation_dir,
        conversation_to_dict,
        conversation_name,
        date=formatted_datetime,
        conversation_id=conversationID
        )
    
    json_converted = json.dumps(conversation_to_dict)
    
    if overwrite_file(filename=conversation_dir + conversation_name, overwrite=json_converted):
        # print('\033[96m' + "File overwritten successfully." + '\033[0m')
        return

def save_summary(*, summary_buffer: str, user,conversationID=None):
    conversation_summary_to_dict=[]
    _,summary_dir=get_conversation_directories()
    summary_name = user + "-summary.txt"
    if conversationID:
        summary_name=user+"-summary.json"
        _,summary_dir=get_conversation_directories(isConversationWithID=True)
        print("saving in conversation id summary")
        if os.path.exists(summary_dir + summary_name):
            summary_retrieved = read_file(filename=summary_dir + summary_name)
            conversation_summary_to_dict = json.loads(summary_retrieved)
        # Check if the conversationID already exists
        existing_entry = next((item for item in conversation_summary_to_dict if item['id'] == conversationID), None)
        if existing_entry:
            existing_entry['message'] = summary_buffer
        else:
            conversation_summary_to_dict.append({
                "id": conversationID,
                "message": summary_buffer
            })
        json_converted = json.dumps(conversation_summary_to_dict)
        
        if overwrite_file(filename=summary_dir + summary_name, overwrite=json_converted):
            return
    
    else:
        if overwrite_file(filename=summary_dir + summary_name, overwrite=summary_buffer):
            return

def get_conversation_chain_video_transcriptions(*, vectorstore, prompt_template: str):
    ## OpenAI api
    # llm = ChatOpenAI()

    ## Azure OpenAI api
    llm = AzureChatOpenAI(azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"))

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key="answer"
    )

    conversationChain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt_template},
        # verbose=True
    )

    return conversationChain

def get_output_from_json_video_transcriptions(*, user_input: str, vector_store) -> str:
    prompt_template = """Use the following pieces of context to answer the question at the end. \
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    Also, provide the key from which you are taking the answer:

    {context}

    Question: {question}
    Helpful Answer:
    ID key:"""
    PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    conversationChain = get_conversation_chain_video_transcriptions(
        vectorstore=vector_store,
        prompt_template=PROMPT,
        )    
    bot_response = handle_bot_output(user_input=user_input, conversationChain=conversationChain)

    return bot_response

def output_parsing_video_transcriptions(*, bot_response: str) -> None:
    """ output examples:
    "videoId": "J8ibae45Yw8"
    "videoId": "None"
    """
    answer_schema = ResponseSchema(name='answer',
        description="The text is a correct answer from a previous answer or it doesn't know?"
    )
    key_schema = ResponseSchema(name='key',
        description='key of random string of characters. Use None if no key was provided in the text.'
    )

    response_schemas = [answer_schema, key_schema]
    parser = StructuredOutputParser.from_response_schemas(response_schemas=response_schemas)
    format_instructions = parser.get_format_instructions()
    # print(format_instructions)

    template = """ 
    Interpretate the text and evaluate the text.
    answer: is the text an actual answer?
    key: Does text contains a key with random string of characters? Use exactly one key/word.

    Just return JSON, do not add ANYTHING, NO INTERPRETATION!

    Text: {input}

    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_template(template=template)
    format_instructions = parser.get_format_instructions()
    messages = prompt.format_messages(
        input=bot_response,
        format_instructions=format_instructions,
    )

    ## OpenAI api
    # llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    ## Azure OpenAI api
    llm = AzureChatOpenAI(temperature=0, azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"))

    bot_response_schema = llm.invoke(messages)
    # print(bot_response_schema)

    bot_response_dict = parser.parse(bot_response_schema.content)
    # print(bot_response_dict)

    return bot_response_dict

def get_classification_chain(*, userInput) -> None:
    classification_template = PromptTemplate.from_template(
        """
        Your goal is to classify user questions about dishwasher
        You are given a context and a problem in the delimiters <> below.
        Classify the problem based on the context below
        # instructions
         - If question is related to Dishwasher , its problem or usages , classify as "BOSCH_dishwasher"
         - If question is general greetings , followup question classify as "Greeting"
         - If question is not related to Dishwasher or above conversation classify as "Offtopic"
         - return category of the question in a single word
         # context
           Bosch dishwasher 
           <Question :{question}>
        """
    )

    classification_chain = (
            classification_template
            # | ChatOpenAI(temperature=0) # OpenAI
            | AzureChatOpenAI(azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"), temperature=0) ## Azure OpenAI api
            | StrOutputParser()
        )

    return classification_chain

def offtopic_chain():
    """ Simple LLM chain """
    ## OpenAI
    # llm = OpenAI(model_name="gpt-3.5-turbo-instruct")

    ## Azure OpenAI
    llm = AzureOpenAI(
        azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"),
        # azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),     
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),       
        # api_version="2024-05-01-preview"
    )

    template = """
    You are a gentle BOSCH assistant, be friendly with user queries and always ask him how can you help him.
    If user question is in another language, translate it into English and then answer in English, ALWAYS answer in English.

    Human: {question}
    AI Assistant:"""

    prompt_template = ChatPromptTemplate.from_template(template=template)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    return chain

def azure_openai_offtopic_chain():
    """ Simple Azure OpenAI call """
    ## Azure OpenAI api
    llm = AzureChatOpenAI(
        azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"),
        # azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    
    memory = ConversationBufferMemory(
    # memory = ConversationSummaryMemory(
        # llm=llm, memory_key='chat_history', return_messages=True
        llm=llm, memory_key='history', return_messages=True
        )

    bosch_system_template = """You are a gentle BOSCH assistant, be friendly with user queries and always ask him how can you help him.
    If user question is in another language, translate it into English and then answer in English, ALWAYS answer in English.

    Human: {question}
    AI Assistant:"""

    general_user_template = "Question:```{question}```"
    messages = [
                SystemMessagePromptTemplate.from_template(bosch_system_template),
                HumanMessagePromptTemplate.from_template(general_user_template)
    ]
    prompt = ChatPromptTemplate.from_messages( messages )

    # conversationChain = ConversationalRetrievalChain.from_llm(
    # conversationChain = ConversationChain.from_llm(
    conversationChain = ConversationChain(
        llm=llm,
        memory=memory,
        # verbose=True,
        # combine_docs_chain_kwargs={'prompt': prompt}
    )

    return conversationChain

def needs_technical_knowledge_classification_chain() -> str:
    """ This function classifies `Yes` or `No` if previous LLM response needs technical knowledge. """
    classification_template = PromptTemplate.from_template(
        """
        TASK: Technical Knowledge required for dishwasher problem resoultion
        Classes: Yes , No
        Context: Bosch Dishwasher ,classify user questions about dishwasher in technical knowledge required . 
        
        Labeled examples:
        Text:I have e-22 error
        Label:Yes
        
        Text:My dishwasher is making a loud grinding noise during the wash cycle. I've checked the filter and it's clean. What could be causing this?
        Label:Yes
        
        Text:The control panel on my dishwasher is unresponsive. I've tried resetting it, but it's still not working. What are the possible issues?
        Label:Yes
        
        Text: i have error
        Label: No
        
        Text: I dont know how to clean my dishwasher
        Label: No
        
        Please classify following question in the delimiters <> below.
        <Question :{llmResponse}>
        """
    )

    classification_chain = (
            classification_template
            # | ChatOpenAI(temperature=0) # OpenAI
            | AzureChatOpenAI(azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"), temperature=0) ## Azure OpenAI api
            | StrOutputParser()
        )

    return classification_chain