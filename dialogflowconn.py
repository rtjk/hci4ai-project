import flask
from flask import Flask, render_template, session
from google.cloud.dialogflowcx_v3.services.sessions import SessionsClient
from google.cloud.dialogflowcx_v3.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3.types import session
import uuid

from google.oauth2 import service_account

import applogic

app= Flask(__name__)
app.secret_key="ciaone"

project_id = "pneumonia-conversational--sops"
# For more information about regionalization see https://cloud.google.com/dialogflow/cx/docs/how/region
location_id = "europe-west3"
# For more info on agents see https://cloud.google.com/dialogflow/cx/docs/concept/agent
agent_id = "68c2ce4d-06d1-4fd7-9d2c-cd4c8b4eacc1"
agent = f"projects/{project_id}/locations/{location_id}/agents/{agent_id}"
# For more supported languages see https://cloud.google.com/dialogflow/es/docs/reference/language
language_code = "en-us"

@app.route("/")
def index():
    flask.session['session_id'] = uuid.uuid4()
    return render_template("index.html")

@app.route('/dialog_ask', methods=['POST'])
def mainfunction():
    text = flask.request.json.get("text")
    json_response = detect_intent_texts(text)
    response = applogic.handle_response(json_response)
    return response

def detect_intent_texts(text):
    """Returns the result of detect intent with text as input.
    Using the same `session_id` between requests allows continuation
    of the conversation."""

    session_path = f'{agent}/sessions/{flask.session["session_id"]}'
    print(f"Session path: {session_path}\n")
    client_options = None
    agent_components = AgentsClient.parse_agent_path(agent)
    location_id = agent_components["location"]
    api_endpoint = f"{location_id}-dialogflow.googleapis.com:443"
    client_options = {"api_endpoint": api_endpoint}
    credentials = service_account.Credentials.from_service_account_file(
        "data/pneumonia-conversational--sops-f92d986fcd88.json")
    session_client = SessionsClient(client_options=client_options, credentials=credentials)

    text_input = session.TextInput(text=text)
    query_input = session.QueryInput(text=text_input, language_code=language_code)
    request = session.DetectIntentRequest(
        session=session_path, query_input=query_input
    )

    response = session_client.detect_intent(request=request)

    return response.query_result

if __name__ == '__main__':
    app.run(port=8000)