from flask import Flask, request, jsonify
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os
import traceback

app = Flask(__name__)

@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello Darshan"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message")
        agentid = data.get("agentid")
        threadid = data.get("threadid")

        if not message or not agentid:
            return jsonify({"error": "message and agentid are required"}), 400

        endpoint ="https://excelagent-project-resource.services.ai.azure.com/api/projects/excelagent-project"
        if not endpoint:
            return jsonify({"error": "Missing AIPROJECT_ENDPOINT env var"}), 500

        project_client = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=endpoint,
        )

        agent = project_client.agents.get_agent(agentid)

        if not threadid:
            try:
                thread_response = project_client.agents.create_thread()
                thread_id = thread_response.id
            except AttributeError:
                thread_response = project_client.agents.threads.create()
                thread_id = thread_response.id
        else:
            thread_id = threadid

        project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        project_client.agents.runs.create_and_process(
            thread_id=thread_id,
            agent_id=agent.id
        )

        messages = list(project_client.agents.messages.list(thread_id=thread_id))
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        if assistant_messages:
            assistant_message = assistant_messages[-1]
            assistant_text = " ".join(
                part.get("text", {}).get("value", "") for part in assistant_message.get("content", []) if "text" in part
            )
        else:
            assistant_text = "No assistant message found."

        return jsonify({"response": assistant_text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
