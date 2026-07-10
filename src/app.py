import asyncio
import os
from typing import TYPE_CHECKING

import ollama
from bs4 import BeautifulSoup
from resonate.resonate import Resonate
from selenium import webdriver

if TYPE_CHECKING:
    from resonate.context import Context


class NetworkResolutionError(Exception):
    """Permanent DNS resolution failure. Do not retry."""


async def downloadAndSummarize(ctx: "Context", params: dict) -> str:
    url = params["url"]
    usable_id = params["usable_id"]
    email = params["email"]
    print(f"beginning work on {url}")
    # Download the content from the URL and save it to a file
    filename = await ctx.run(download, usable_id, url)
    while True:
        # Summarize the content of the file
        summary = await ctx.run(summarize, filename)

        # Create a durable promise to block on human confirmation
        promise_future = ctx.promise()
        promise_id = await promise_future.id()

        # Send email with summary and confirmation/rejection links
        await ctx.run(send_email, summary, email, promise_id)

        # Wait for the promise to be resolved (confirmed or rejected)
        confirmed = await promise_future
        if confirmed:
            break

        print("summary was rejected, re-summarizing")
    print("summary confirmed, workflow complete.")
    return summary


def download(_, usable_id: str, url: str) -> str:
    filename = f"{usable_id}.txt"
    print(f"downloading {url} and saving to {filename}")
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return filename
    driver = webdriver.Chrome()

    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content = soup.get_text()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        driver.quit()
        return filename
    except Exception as e:
        driver.quit()
        if "net::ERR_NAME_NOT_RESOLVED" in str(e):
            raise NetworkResolutionError(f"DNS failure: {e}") from e
        raise Exception(f"Failed to download data: {e}")


def summarize(_, filename: str) -> str:
    print(f"summarizing content from {filename}")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            file_content = f.read()

        options: ollama.Options | None = None
        result = ollama.chat(
            model="llama3.1",
            messages=[
                {
                    "role": "system",
                    "content": "You review text scraped from a website and summarize it. Ignore text that does not support the narrative and purpose of the website.",
                },
                {"role": "user", "content": f"Content to summarize: {file_content}"},
            ],
            options=options,
        )
        return result.message.content
    except Exception as e:
        raise Exception(f"Failed to summarize content: {e}")


def send_email(_, summary: str, email: str, promise_id: str) -> None:
    print(f"Summary: {summary}")
    print(
        f"Click to confirm: http://localhost:9000/confirm?confirm=true&promise_id={promise_id}"
    )
    print(
        f"Click to reject: http://localhost:9000/confirm?confirm=false&promise_id={promise_id}"
    )
    print(f"Email sent to {email} with summary and confirmation links.")


async def main() -> None:
    resonate = Resonate(
        url=os.environ.get("RESONATE_URL", "http://localhost:8001"),
        group="worker",
    )
    resonate.register(downloadAndSummarize)
    resonate.register(download)
    resonate.register(summarize)
    resonate.register(send_email)

    print("Worker started. Waiting for work...")
    try:
        await asyncio.Event().wait()
    finally:
        await resonate.stop()


if __name__ == "__main__":
    asyncio.run(main())
