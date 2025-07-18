from flask import Flask, request, jsonify
from resonate import Resonate
import json
import re

app = Flask(__name__)

resonate = Resonate.remote(
    group="gateway",
)


# Invoke the downloadAndSummarize workflow
@app.route("/summarize", methods=["POST"])
def summarize_route_handler():
    try:
        data = request.get_json()
        if "url" not in data and "email" not in data:
            return jsonify({"error": "URL and email required"}), 400

        params = {}
        params["url"] = data["url"]
        params["email"] = data["email"]
        params["usable_id"] = clean(data["url"])

        # Use Resonate's Async RPC to start the workflow
        _ = resonate.options(target="poll://any@worker").rpc(
            f"downloadAndSummarize-{params['usable_id']}",
            "downloadAndSummarize",
            params,
        )

        return jsonify({"summary": "workflow started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Handle the confirmation of summarization
@app.route("/confirm", methods=["GET"])
def confirm_route_handler():
    try:

        promise_id = request.args.get("promise_id")
        confirm = request.args.get("confirm")

        if not promise_id or confirm is None:
            return jsonify({"error": "url and confirmation params are required"}), 400

        confirm = confirm.lower() == "true"

        resonate.promises.resolve(
            id=promise_id,
            data=json.dumps(confirm),
        )
        if confirm:
            return jsonify({"message": "Summarization confirmed."}), 200
        else:
            return jsonify({"message": "Summarization rejected."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Clean the URL to create a usable ID that can be used in file names
def clean(url):
    tmp = re.sub(r"^https?://", "", url)
    return tmp.replace("/", "-")


def main():
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
