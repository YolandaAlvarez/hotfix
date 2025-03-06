from flask import Blueprint, request, jsonify, abort

from dotenv import load_dotenv
import os
from langchain_openai import AzureChatOpenAI
from openai import RateLimitError
from pydantic import ValidationError

from utils.constants import DB_TRANSCRIPTIONS
from utils.video_retriever.video_id_retriever import VideoIDRetriever
from models import GetVideoRequestModel

video_bp = Blueprint('video', __name__, template_folder="templates")

# setup_logging()
load_dotenv()

llm = AzureChatOpenAI(azure_deployment=os.environ.get("AZURE_CHAT_DEPLOYMENT"))
videoRetriever = VideoIDRetriever(llm=llm, vectorDBPath=DB_TRANSCRIPTIONS)

@video_bp.route('get-video', methods=['GET', 'POST'])
def update_conversation_video():
    """ Retrieve related YT ID video. Not storing into user conversation yet.""" 
    # Data Validation
    if not request.args.get('user'):
        return jsonify({"error": "Missing user."}), 400
    
    data = request.json
    data['user'] = request.args.get('user')

    try:
        requestData = GetVideoRequestModel(**request.json)
    except ValueError as e:
        abort(400, description=str(e))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    try:
        idResponse = videoRetriever.get_video_id(requestData.human)
    except RateLimitError as e:
        return jsonify({"error": "OpenAI RateLimitError."}), 429
    except Exception as e:
        return jsonify({"error": "Server error."}), 500

    return jsonify({"videoId": idResponse}), 201
