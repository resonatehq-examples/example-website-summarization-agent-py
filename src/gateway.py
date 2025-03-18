from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate import Resonate, Context
from resonate.targets import poll
from flask import Flask, request, jsonify
import json
import re

app = Flask(__name__)

# Initialize Resonate and connect to remote storage and a task source
resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    task_source=Poller(url="http://localhost:8002", group="gateway")
)


# Register a dispatch function to start the workflow
# This is temporary and won't be needed in future versions of the SDK
@resonate.register
def dispatch(ctx: Context, url: str, clean_url: str, email: str):
    yield ctx.rfi("downloadAndSummarize", url, clean_url, email).options(
        send_to=poll("summarization-nodes")
    )
    return


@app.route("/summarize", methods=["POST"])
def summarize_route_handler():
    try:
        # Extract JSON data from the request
        data = request.get_json()
        if "url" not in data and "email" not in data:
            return jsonify({"error": "URL and email required"}), 400

        # Extract the URL from the request
        url = data["url"]
        email = data["email"]
        clean_url = clean(url)

        dispatch.run(f"downloadAndSummarize-{clean_url}", url, clean_url, email)

        return jsonify({"summary": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/confirm", methods=["GET"])
def confirm_email_route_handler():
    global store
    try:
        # Extract parameters from the request
        promise_id = request.args.get("promise_id")
        confirm = request.args.get("confirm")

        # Check if the required parameters are present
        if not promise_id or confirm is None:
            return jsonify({"error": "url and confirmation params are required"}), 400

        # Convert to boolean
        confirm = confirm.lower() == "true"

        # Resolve the promise
        resonate.promises.resolve(
            id=promise_id,
            ikey=None,
            strict=False,
            headers=None,
            data=json.dumps(confirm),
        )
        if confirm:
            return jsonify({"message": "Summarization confirmed."}), 200
        else:
            return jsonify({"message": "Summarization rejected."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def clean(url):
    tmp = re.sub(r"^https?://", "", url)
    return tmp.replace("/", "-")


def main():
    app.run(host="127.0.0.1", port=5000)
    print("Serving HTTP on port 5000...")


if __name__ == "__main__":
    main()
