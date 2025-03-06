import logging
import json
import logging.config
import pathlib
import os

from utils.constants import DB_CONVERSATION, DB_SUMMARIES, DB_SUMMARIES_WITH_IDS, DB_USERS_CONVERSATIONS_WITH_IDS
import uuid

logger = logging.getLogger("logs")

def setup_logging() -> None:
    """ Levels to choose for config: 
    - debug
    - info
    - warning
    - error
    - critical
    """
    create_directory(folder="logs")

    config_file = pathlib.Path("config/logging_config.json")
    with open(config_file) as data:
        config = json.load(data)

    logging.config.dictConfig(config=config)

def create_directory(*, folder: str):
    """ Creates folder in case it doesn't exist. """
    if not os.path.exists(f"./{folder}/"):
        os.makedirs(f"./{folder}")
        logger.info(f"{folder}/ created.")

        return True
    return False


def get_conversation_directories(isConversationWithID=False):
    conversation_dir = DB_USERS_CONVERSATIONS_WITH_IDS if isConversationWithID else DB_CONVERSATION
    summary_dir = DB_SUMMARIES_WITH_IDS if isConversationWithID else DB_SUMMARIES
    return conversation_dir, summary_dir


def overwrite_file(*, filename: str, overwrite: str):
    """ Overwrite any txt file.

    Parameters example:
    .. code-block:: python
    if overwrite_file('db/text.txt', 'New text')
        print("File overwritten successfully.")
    """
    file = open(f'{filename}', 'w')
    file.write(f'{overwrite}')
    file.close()

    return True

def read_file(*, filename: str):
    file = open(f'{filename}', 'r')
    data = file.read()
    file.close()
    return data

def get_all_conversation_ids(dir_name,conversation_name):
    file=dir_name+conversation_name
    conversation_ids=[]
    if os.path.exists(file):
        print(f"The file {dir_name} exists.")
        conversation_data = read_file(filename=file)
        data_converted = json.loads(conversation_data)
        for conversation in data_converted:
            conversation_ids.append(conversation["conversation_id"])
            
    return conversation_ids

def get_conversation_with_id(dir_name,conversation_name,conversation_id=None):
    file=dir_name+conversation_name
    if os.path.exists(file):
        print(f"The file {dir_name} exists.")
        conversation_data = read_file(filename=file)
        data_converted = json.loads(conversation_data)
        for conversation in data_converted:
            print(f"Checking id {conversation_id} exist or not in {conversation}")
            if conversation["conversation_id"] == conversation_id:
                print("conversation id found")
                return conversation
    else:
        print("Conversation doesnt exist")
        return None
    
    

def create_conversation_content(conversation_dir,dict_conversation,conversation_name, date, conversation_id=None):
    """ Necessary keys for conversations. """
    
    filename = conversation_dir + conversation_name
    
    history_exists = False
    conversation_id_exists = False
    data_converted = []
    
    if os.path.exists(filename):
        print(f"The file {filename} exists.")
        conversation_data = read_file(filename=conversation_dir+conversation_name)
        data_converted = json.loads(conversation_data)
        history_exists = True
        for conversation in data_converted:
            print(f"""Checking id {conversation["conversation_id"]}exist or not""")
            if conversation["conversation_id"] == conversation_id:
                print("conversation id found , appending now")
                conversation["conversation"]= dict_conversation
                conversation_id_exists = True
                break
    
    print(f"History {history_exists} and conversation {conversation_id_exists}")
        
    # If conversation_id does not exist, create a new entry
    if not history_exists or not conversation_id_exists:
        print(f"Doesnt exist , history {history_exists} and conversation_id_exists {conversation_id_exists} , storing new again ")
        new_entry = {
            "conversation_date": date,
            "conversation_id": conversation_id if conversation_id else str(uuid.uuid4()),
            "conversation": [dict_conversation],
            "conversation_feedback": "NA"
        }
        data_converted.append(new_entry)
    
    print(len(data_converted))    
    
    return data_converted

def add_feedback(dict_conversation):
    """ Adds 'feedback' and 'id' keys to data conversation. """ 

    dict_conversation[-1]["data"]["feedback"] = "na"
    if len(dict_conversation) < 3:
        dict_conversation[-1]["data"]["id"] = 1
    else:
        last_response = len(dict_conversation)-3
        last_id = int(dict_conversation[last_response]["data"]["id"])
        dict_conversation[-1]["data"]["id"] = last_id + 1
    return dict_conversation

def update_conversartion_feedback(conversation_dir,user, feedback,conversationID):
    """ Updates the 'feedback' of a response, given its 'response_id' and 'user'. """
    conversation_name = user+"-conversation.json"

    if not os.path.exists(conversation_dir+conversation_name):
        return {"False": "No user was found."}
        
    conversation_retrieved = read_file(filename=conversation_dir+conversation_name)
    conversation_retrieved_converted = json.loads(conversation_retrieved)

    for conversation in conversation_retrieved_converted:
        if str(conversation["conversation_id"]) == str(conversationID):
            conversation["conversation_feedback"] = feedback
            json_converted = json.dumps(conversation_retrieved_converted)
            print(json_converted)
            if overwrite_file(filename=conversation_dir+conversation_name, overwrite=json_converted):
                return {"true": "Succesfully updated."}
            else:
                return {"error": "Cann't overwrite file."}
        
    return {"False": "No response_id was found."}

def change_feedback(user, response_id, feedback):
    """ Updates the 'feedback' of a response, given its 'response_id' and 'user'. """
    conversation_name = user+"-conversation.json"

    if not os.path.exists(DB_CONVERSATION+conversation_name):
        return {"false": "No user was found."}
        
    conversation_retrieved = read_file(filename=DB_CONVERSATION+conversation_name)
    conversation_retrieved_converted = json.loads(conversation_retrieved)

    for conversation in conversation_retrieved_converted:
        if str(conversation["data"]["id"]) == str(response_id):
            conversation["data"]["feedback"] = feedback 

            json_converted = json.dumps(conversation_retrieved_converted)

            if overwrite_file(filename="db/"+conversation_name, overwrite=json_converted):
                return {"true": "Succesfully updated."}
            else:
                return {"error": "Cann't overwrite file."}
        
    return {"false": "No response_id was found."}

def add_key_value_to_conversation(*, dictConversation: dict, keyName: str, value) -> dict:
    """ Add a new key `keyName` and it's `value` at the end of the conversation data dict. """
    dictConversation[-1]["data"][keyName] = value
    return dictConversation

def delete_files_inside_directory(*args: str, fileExtension: str = None) -> bool:
    """ 
    Deletes specific or all files inside a directory. 
    
    :param *args: One or more directory paths as strings where files need to be deleted. Arg example: "db/_Conversations/"
    :param fileExtension: The file extension to filter which files to delete. If None, all files in the directory will be deleted.
    :return: True if all specified files are deleted successfully, False if any exception occurs.

    Example:
    .. code-block:: python
        from utils.utilites import delete_files_inside_directory

        delete_files_inside_directory("db/_Conversations/", fileExtension=".json")
    """
    for directory in args:
        # Verify that directory string ends with a slash '/'
        if not directory.endswith("/"):
            directory += "/"

        for file in os.listdir(directory):
            try:
                # Remove by file extension
                if fileExtension:
                    if file.endswith(fileExtension):
                        os.remove(directory + file)
                        # print(f"File {directory}{file} deleted successfully.")

                # Remove all files inside directory
                else:
                    os.remove(directory + file)
                    # print(f"File {directory}{file} deleted successfully.")

            except FileNotFoundError as e:
                print(f"Exception: {e}")
                logger.error(f"File {directory}{file} not found.")
                return False
            except Exception as e:
                logger.error(f"Exception: {e}")
                return False

    return True