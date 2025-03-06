from flask import Blueprint, request, jsonify, Response, abort

import os
from dotenv import load_dotenv
import json
from pydantic import ValidationError

from models.feedback_request_model import FeedbackRequestModel
from models.update_conversation_request_model import UpdateConversationRequestModel
from models.get_conversation_request_model import GetConversationRequestModel, GetSummaryRequestModel

from utils.vectorstore import load_vector_store
from utils.utilities import get_conversation_directories, get_conversation_with_id, get_all_conversation_ids,read_file, setup_logging, logger, change_feedback, create_directory, delete_files_inside_directory, update_conversartion_feedback
from utils.langchain_utils import (
    get_conversation_chain,get_start_conversation_chain,handle_bot_output, save_chat_history, save_summary,
    get_output_from_json_video_transcriptions, get_conversation_chain_video_transcriptions,
    output_parsing_video_transcriptions, get_classification_chain, needs_technical_knowledge_classification_chain,
    offtopic_chain, azure_openai_offtopic_chain
)

from openai import RateLimitError

conversation_bp = Blueprint('conversation', __name__, 
    # template_folder="templates"
    )

setup_logging()
load_dotenv()

## This lines are needed for OpenAI API, uncomment them unless you are using Azure OpenAI.
# AM_I_IN_A_DOCKER_CONTAINER: bool = os.environ.get("AM_I_IN_A_DOCKER_CONTAINER", False)
# if not AM_I_IN_A_DOCKER_CONTAINER:
#     os.environ['HTTP_PROXY'] = f'http://{os.environ.get("BOSCH_USER")}:{os.environ.get("BOSCH_PASSWORD")}@rb-proxy-na.bosch.com:8080'
#     os.environ['HTTPS_PROXY'] = f'http://{os.environ.get("BOSCH_USER")}:{os.environ.get("BOSCH_PASSWORD")}@rb-proxy-na.bosch.com:8080'

# need to move this 
create_directory(folder='db')
create_directory(folder='db/_Conversations')
create_directory(folder='db/_Summaries')
create_directory(folder='db/_UsersConversationsWithIds')
create_directory(folder='db/_UserConversationsSummaries')


vectorStore = load_vector_store(path="db/faiss_default")

logger.info("Conversation Blueprint loaded successfully.")

@conversation_bp.route('<user>/get-summary/<conversationID>', methods=['GET'])
def get_summary_id(user,conversationID):
    # Data Validation
    if not user:
        return jsonify({"error": "Missing user."}), 400
    
    if not conversationID:
        return jsonify({"error": "Missing conversation id."}), 400
    data: dict = {}
    data['user'] = user
    
    _,summaries=get_conversation_directories(isConversationWithID=True)

    summary_name = user + "-summary.json"
    
    if not os.path.exists(summaries+summary_name):
        return Response('{"error":"No summary was found for this user"}', status=404, mimetype='application/json')
    
    summary_data = read_file(filename=summaries+summary_name)
    summary_retrieved_converted = json.loads(summary_data)
    summary_retrieved = next((item['message'] for item in summary_retrieved_converted if item['id'] == conversationID), None)
    if not summary_retrieved:
        return Response('{"error":"No summary was found for this id"}', status=404, mimetype='application/json')
    
    response: dict = {"summary": summary_retrieved}

    return jsonify(response), 200

@conversation_bp.route('get-summary', methods=['GET'])
def get_summary():
    # Data Validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    data: dict = {}
    data['user'] = request.args.get('user')
    
    _,summaries=get_conversation_directories(isConversationWithID=False)

    try:
        requestData = GetConversationRequestModel(**data)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    summary_name = requestData.user + "-summary.txt"
    
    if not os.path.exists(summaries+summary_name):
        return Response('{"error":"No summary was found."}', status=404, mimetype='application/json')
    
    summary_data = read_file(filename=summaries+summary_name)
    response: dict = {"summary": summary_data}

    return jsonify(response), 200


@conversation_bp.route('/<user>/get-conversation-ids', methods=['GET'])
def get_conversation_ids(user):
    # Data Validation
    if not user:
        return jsonify({"error": "Missing user."}), 400
    
    data: dict = {}
    data['user'] = user
    conversation_dir,summaries=get_conversation_directories(isConversationWithID=True)

    try:
        requestData = GetConversationRequestModel(**data)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    conversation_name = requestData.user + "-conversation.json"
    summary_name = requestData.user + "-summary.txt"

    if not os.path.exists(conversation_dir+conversation_name) and not os.path.exists(summaries+summary_name):
        return jsonify({"error": "No conversation was found."}), 404
    
    conversation_data = get_all_conversation_ids(conversation_dir,conversation_name)
    if len(conversation_data) == 0:
        return jsonify({"error": "No conversation id was found."}), 404
    data_converted = json.loads(json.dumps(conversation_data))

    return jsonify(data_converted), 200


@conversation_bp.route('/<user>/get-conversation/<conversationID>', methods=['GET'])
def get_conversation_id(user,conversationID):
    """ Get stored conversation if existing. """
    # Data Validation
    if not user:
        return jsonify({"error": "Missing user."}), 400
    
    if not conversationID:
        return jsonify({"error": "Missing conversation id."}), 400
    
    data: dict = {}
    data['user'] = user
    
    conversation_dir,summaries=get_conversation_directories(isConversationWithID=True)

    try:
        requestData = GetConversationRequestModel(**data)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400
    
    conversation_name = requestData.user + "-conversation.json"
    summary_name = requestData.user + "-summary.txt"

    if not os.path.exists(conversation_dir+conversation_name) and not os.path.exists(summaries+summary_name):
        return jsonify({"error": "No user was found."}), 404
    
    conversation_data = get_conversation_with_id(conversation_dir,conversation_name,conversation_id=conversationID)
    if not conversation_data:
        return jsonify({"error": "No conversation id was found."}), 404
    data_converted = json.loads(json.dumps(conversation_data))

    return jsonify(data_converted), 200


@conversation_bp.route('get-conversation', methods=['GET'])
def get_conversation():
    """ Get stored conversation if existing. """
    # Data Validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    data: dict = {}
    data['user'] = request.args.get('user')
    
    conversation_dir,summaries=get_conversation_directories(isConversationWithID=False)

    try:
        requestData = GetConversationRequestModel(**data)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400
    
    conversation_name = requestData.user + "-conversation.json"
    summary_name = requestData.user + "-summary.txt"

    if not os.path.exists(conversation_dir+conversation_name) and not os.path.exists(summaries+summary_name):
        return jsonify({"error": "No conversation was found."}), 404
    
    conversation_data = read_file(filename=conversation_dir+conversation_name)
    data_converted = json.loads(conversation_data)

    return jsonify(data_converted), 200

@conversation_bp.route('update-conversation', methods=['POST'])
def update_conversation():
    """ Retrieve LLM response with stored conversation summary context """
    # Data Validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    user = request.args.get('user')
    data = request.json
    data['user'] = request.args.get('user')

    if request.args.get('applianceVIB'):
        data['applianceVIB'] = request.args.get('applianceVIB')

    try:
        requestData = UpdateConversationRequestModel(**request.json)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # RAG
    conversationChain = get_conversation_chain(vectorStore=vectorStore, user=user)
    try:
        bot_output = handle_bot_output(user_input=requestData.human, conversationChain=conversationChain)
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    save_chat_history(extracted_messages=conversationChain.memory.chat_memory.messages, user=user)
    save_summary(summary_buffer=conversationChain.memory.buffer, user=user)

    return jsonify({"ai": f"{bot_output}"}), 201

@conversation_bp.route('update-conversation-video', methods=['POST'])
def update_conversation_video():
    """ Retrieve LLM response with stored conversation summary context, then look for stored related YT video """ 
    # Data validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    user = request.args.get('user')
    data = request.json

    if not data.get('human') or not len(data.get('human')) > 1 or not data['human'].strip():
        return jsonify({"error": "Invalid data."}), 400
    
    if request.args.get('applianceVIB'):
        ...

    # RAG
    conversationChain = get_conversation_chain(vectorStore=vectorStore, user=user)
    bot_output = handle_bot_output(user_input=data.get('human'), conversationChain=conversationChain)
    
    # Transcriptions
    vector_store_transcriptions = load_vector_store(path="./db/transcriptions")
    bot_output_video = get_output_from_json_video_transcriptions(user_input=data.get('human'), vector_store=vector_store_transcriptions)
    bot_response_dict = output_parsing_video_transcriptions(bot_response=bot_output_video)
    
    save_chat_history(extracted_messages=conversationChain.memory.chat_memory.messages, user=user, videoId=bot_response_dict['key'])
    save_summary(summary_buffer=conversationChain.memory.buffer, user=user)

    return jsonify({"ai": f"{bot_output}", "videoId": bot_response_dict['key']}), 201

@conversation_bp.route('delete-conversation', methods=['DELETE'])
def delete_conversation() -> Response:
    """ 
    Delete stored conversation and summary if existing.  <br><br>
    Send keyword all** as user query param in order to delete all stored conversations.
    """
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400

    user = request.args.get('user')
    
    conversation_dir,summaries=get_conversation_directories(isConversationWithID=False)
    conversation_dir_id,summaries_dir_id=get_conversation_directories(isConversationWithID=True)

    if user == "all**":
        try:
            delete_files_inside_directory(conversation_dir, fileExtension=".json")
            delete_files_inside_directory(summaries, fileExtension=".txt")
            # deleting for conversation id and summaries
            delete_files_inside_directory(conversation_dir_id, fileExtension=".json")
            delete_files_inside_directory(summaries_dir_id, fileExtension=".json")
        except Exception as e:
            logger.error(f"Error deleting all conversations: {e}")
            return jsonify({"error": f"Error deleting all conversations: {e}"}), 500
        else:
            logger.info(f"All conversations from {conversation_dir} deleted succesfully.")
            return Response('{"success":"All stored conversations deleted succesfully."}', status=200, mimetype='application/json')
    
    requirements = [f"{conversation_dir_id}{user}-conversation.json", f"{summaries_dir_id}{user}-summary.json"]
    if os.path.exists(requirements[0]) and os.path.exists(requirements[1]):
        os.remove(requirements[0])
        os.remove(requirements[1])
    else:
        return Response('{"error":"No conversation was found."}', status=404, mimetype='application/json')
    
    return Response('{"success":"Conversation deleted succesfully"}', status=200, mimetype='application/json')


@conversation_bp.route('<user>/update-conversation-feedback/<conversationID>', methods=['POST'])
def update_conversation_feedback(user,conversationID):
    """ Updates the feedback of a response for a user. """ 
    try:
        feedback_request = FeedbackRequestModel(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400   
    
    if not user:
        return jsonify({"error": "Missing user."}), 400
    
    if not conversationID:
        return jsonify({"error": "Missing conversation id."}), 400
    
    conversation_dir,_=get_conversation_directories(isConversationWithID=True)
    feedback = feedback_request.feedback
    
    result = update_conversartion_feedback(conversation_dir, user,feedback,conversationID)
    if result.get("true"):
        return jsonify(result), 201

    return jsonify(result), 400

@conversation_bp.route('update-feedback', methods=['POST'])
def update_feedback():
    """ Updates the feedback of a response for a user. """ 
    try:
        feedback_request = FeedbackRequestModel(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400    
    # Validate if all parameters are available
    user = feedback_request.user
    feedback = feedback_request.feedback
    response_id = feedback_request.responseId
    
    result = change_feedback(user, response_id, feedback)
    if result.get("true"):
        return jsonify(result), 201

    return jsonify(result), 400


# Adding conversation id
@conversation_bp.route('/<user>/start-conversation/<conversationID>', methods=['POST'])
def start_conversation(user,conversationID) -> None:
    """ `Beta Endpoint`. \n
    Classify the input and route to the correct chain. """
    # Data Validation
    if not user:
        return jsonify({"error": "Missing user."}), 400
    
    if not conversationID:
        return jsonify({"error": "Missing conversation id."}), 400
    
    data = request.json
    data['user'] = user          
    
    if request.args.get('applianceVIB'):
        data['applianceVIB'] = request.args.get('applianceVIB')    

    try:
        requestData = UpdateConversationRequestModel(**request.json)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # RAG
    """ Chain 1: Classification Chain: route to it's correct chain """
    classificationChain = get_classification_chain(userInput=requestData.human)

    try:
        routedResponse = classificationChain.invoke({"question": requestData.human})
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    def custom_route(info: str) -> None:
        print(info)
        if "greeting" in info.lower():
            """ Chain 2 "Greeting" """
            print("This has to be handled with Greeting")
            # conversationChain_Greeting = offtopic_chain() # OpenAI gpt-3.5-turbo-instruct
            conversationChain_Greeting = azure_openai_offtopic_chain()
            return conversationChain_Greeting
        
        elif "dishwasher" in info.lower():
            """ Chain 3 "BOSCH_dishwasher": BOSCH dishwasher info """
            print("This has to be handled with BOSCH_dishwasher")
            conversationChain = get_start_conversation_chain(vectorStore=vectorStore, user=user,conversationID=conversationID)
            return conversationChain
        
        else:
            """ Chain 4 "Offtopic" | "General Knowledge" : Offtopic queries """
            # conversationChain_Offtopic = offtopic_chain()
            # return conversationChain_Offtopic
            return
    
    if routedResponse == "Offtopic":
        return jsonify({"ai": None, "source": "General Knowledge"}), 201

    classifiedChain = custom_route(routedResponse)
    try:
        bot_output = handle_bot_output(user_input=requestData.human, routedResponse=routedResponse, conversationChain=classifiedChain)
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    if "dishwasher" in routedResponse.lower():
        # we need to change this
            if "please visit in bosch home appliances page" in bot_output.lower():
                return jsonify({"ai": f"{bot_output}", "source": None}), 201
            
            routedResponse = "User Manual"

            needsTechnicalChain = needs_technical_knowledge_classification_chain()
            needsTechnicalResponse = needsTechnicalChain.invoke({"llmResponse": bot_output})

            print(f"needsTechnicalResponse: {needsTechnicalResponse}")
            if "yes" in needsTechnicalResponse.lower():
                print("This response needs Technical Knowledge")
                routedResponse += " + Technical Knowledge"

            save_chat_history(extracted_messages=classifiedChain.memory.chat_memory.messages, user=user,conversationID=conversationID, source=routedResponse)
            save_summary(summary_buffer=classifiedChain.memory.buffer, user=user,conversationID=conversationID)


    return jsonify({"ai": f"{bot_output}", "source": routedResponse}), 201



# New classification pipeline
@conversation_bp.route('update-conversation-classification', methods=['POST'])
def update_conversation_classification() -> None:
    """ `Beta Endpoint`. \n
    Classify the input and route to the correct chain. """
    # Data Validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    user = request.args.get('user')
    data = request.json
    data['user'] = request.args.get('user')

    if request.args.get('applianceVIB'):
        data['applianceVIB'] = request.args.get('applianceVIB')

    try:
        requestData = UpdateConversationRequestModel(**request.json)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    # RAG
    """ Chain 1: Classification Chain: route to it's correct chain """
    classificationChain = get_classification_chain(userInput=requestData.human)

    try:
        routedResponse = classificationChain.invoke({"question": requestData.human})
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    def custom_route(info: str) -> None:
        print(info)
        if "greeting" in info.lower():
            """ Chain 2 "Greeting" """
            print("This has to be handled with Greeting")
            # conversationChain_Greeting = offtopic_chain() # OpenAI gpt-3.5-turbo-instruct
            conversationChain_Greeting = azure_openai_offtopic_chain()
            return conversationChain_Greeting
        
        elif "dishwasher" in info.lower():
            """ Chain 3 "BOSCH_dishwasher": BOSCH dishwasher info """
            print("This has to be handled with BOSCH_dishwasher")
            conversationChain = get_conversation_chain(vectorStore=vectorStore, user=user)
            return conversationChain
        
        else:
            """ Chain 4 "Offtopic" | "General Knowledge" : Offtopic queries """
            # conversationChain_Offtopic = offtopic_chain()
            # return conversationChain_Offtopic
            return
    
    if routedResponse == "Offtopic":
        return jsonify({"ai": None, "source": "General Knowledge"}), 201

    classifiedChain = custom_route(routedResponse)
    try:
        bot_output = handle_bot_output(user_input=requestData.human, routedResponse=routedResponse, conversationChain=classifiedChain)
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    if "dishwasher" in routedResponse.lower():
        # we need to change this
            if "please visit in bosch home appliances page" in bot_output.lower():
                return jsonify({"ai": f"{bot_output}", "source": None}), 201
            
            routedResponse = "User Manual"

            needsTechnicalChain = needs_technical_knowledge_classification_chain()
            needsTechnicalResponse = needsTechnicalChain.invoke({"llmResponse": bot_output})

            print(f"needsTechnicalResponse: {needsTechnicalResponse}")
            if "yes" in needsTechnicalResponse.lower():
                print("This response needs Technical Knowledge")
                routedResponse += " + Technical Knowledge"

            save_chat_history(extracted_messages=classifiedChain.memory.chat_memory.messages, user=user, source=routedResponse)
            save_summary(summary_buffer=classifiedChain.memory.buffer, user=user)


    return jsonify({"ai": f"{bot_output}", "source": routedResponse}), 201