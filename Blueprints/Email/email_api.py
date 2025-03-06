import json
from flask import Blueprint, request, jsonify, abort
from dotenv import load_dotenv
import logging
import os
import Blueprints.Email.aws_smtp as aws_smtp
from flask import request, jsonify
from flask_cors import CORS
from pydantic import BaseModel, EmailStr, ValidationError
from utils.constants import DB_SUMMARIES
from utils.utilities import read_file ,get_conversation_directories

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


email_bp = Blueprint('email', __name__, template_folder="templates")
load_dotenv()

def get_message_by_id(json_data, message_id):
    try:
        messages = json.loads(json_data)
        for message in messages:
            if message.get('id') == message_id:
                return message.get('message')
        return {"error": "Message not found."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data."}
    
def read_summary(summary_dir, summary_name):
    if not os.path.exists(summary_dir+summary_name):
            return "No summary was found."
    return read_file(filename=summary_dir+summary_name)    
    

def summary_content(user,conversationID):
    summary_data = None
    if conversationID:
        summary_name = user + "-summary.json"
        _,summary_dir=get_conversation_directories(isConversationWithID=True)
        data = read_summary(summary_dir=summary_dir,summary_name=summary_name)
        summary = get_message_by_id(data,message_id=conversationID)
        summary_data = (
            f"Conversation ID: {conversationID}\n"
            f"Chat Summary: {summary}")
    
    else:
        _,summary_dir=get_conversation_directories(isConversationWithID=False)
        summary_name = user + "-summary.txt"   
        data= read_summary(summary_dir=summary_dir,summary_name=summary_name) 
        summary_data = data
    return summary_data

# This address must be verified with Amazon SES.


# The character encoding for the email.
CHARSET = "UTF-8"

# Pydantic model for request body
class EmailRequest(BaseModel):
    email: EmailStr
    summary: str

@email_bp.route('send-email', methods=['POST'])
def send_email():
    try:
        if not request.args.get('user'):
            return jsonify({"error": "Missing user."}), 400
        userName = request.args.get('user')
        conversationID=None
        if request.args.get('conversationID'):
            conversationID = request.args.get('conversationID')    
        # Parse and validate request body
        data = request.get_json()
        email_request = EmailRequest(**data)
        aws_smtp.send_email_smtp(email_request.email, "RNA DishCare Customer Service", email_request.summary)
        summary = summary_content(userName,conversationID)
        logger.info(summary)
        aws_smtp.send_email_smtp(None, "RNA DishCare Customer Service", email_request.summary+"   \n   "+summary)
        return jsonify({"message": "Email sent successfully"}), 200
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 500