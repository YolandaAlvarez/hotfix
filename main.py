""" 
Python 3.11.0
pip 22.3

API REST with Flask

@Author: TJO1GA
@Date: 3th April 2024
"""
from flask import Flask, render_template, redirect, jsonify
from flask_cors import CORS

from Blueprints.Conversation.conversation import conversation_bp
from Blueprints.Video.video import video_bp
from Blueprints.Email.email_api import email_bp

app = Flask(__name__)
CORS(app, origins='*')

@app.route('/', methods=['GET'])
def index():
    return redirect(location='/api/docs')

@app.route('/api/docs', methods=['GET'])
def docs():
    return render_template('swaggerui.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify(status="healthy"), 200

app.register_blueprint(conversation_bp, url_prefix="/api/v1/conversation")
app.register_blueprint(video_bp, url_prefix="/api/v1/video")
app.register_blueprint(email_bp, url_prefix="/api/v1/email")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)