import asyncio
import json
import os
import re

from flask import Flask, jsonify, request
from resonate.resonate import Resonate
from resonate.types import Value

app = Flask(__name__)

_RESONATE_URL = os.environ.get("RESONATE_URL", "http://localhost:8001")


def _make_resonate() -> Resonate:
    """Create a short-lived Resonate gateway client for one request."""
    return Resonate(url=_RESONATE_URL, group="gateway")


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

        async def _dispatch():
            r = _make_resonate()
            await asyncio.sleep(0)
            handle = r.options(target="worker").rpc(
                f"downloadAndSummarize-{params['usable_id']}",
                "downloadAndSummarize",
                params,
            )
            if not handle.done():
                await r.stop()
                return jsonify({"summary": "workflow started"}), 200
            result = await handle.result()
            await r.stop()
            return jsonify({"summary": result}), 200

        return asyncio.run(_dispatch())
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

        async def _resolve():
            r = _make_resonate()
            await asyncio.sleep(0)
            await r.promises.resolve(promise_id, Value(data=json.dumps(confirm)))
            await r.stop()

        asyncio.run(_resolve())

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
    app.run(host="127.0.0.1", port=9000)


if __name__ == "__main__":
    main()
