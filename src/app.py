from resonate import Resonate
from threading import Event
from selenium import webdriver
from bs4 import BeautifulSoup
import ollama
import os

resonate = Resonate.remote(
    group="worker",
)


@resonate.register
def downloadAndSummarize(ctx, params):
    url = params["url"]
    usable_id = params["usable_id"]
    email = params["email"]
    print(f"beginning work on {url}")
    # Download the content from the URL and save it to a file
    filename = yield ctx.lfc(download, usable_id, url).options(durable=False,non_retryable_exceptions=(NetworkResolutionError,))
    while True:
        # Summarize the content of the file
        summary = yield ctx.lfc(summarize, filename)

        # Create Durable Promise to block on confirmation
        promise = yield ctx.promise()

        # Send email with summary and confirmation/rejection links
        yield ctx.lfc(send_email, summary, email, promise.id)

        # Wait for summary to be confirmed or rejected / wait for the promise to be resolved
        confirmed = yield promise
        if confirmed:
            break

        print("summary was rejected, re-summarizing")
    print("summary confirmed, workflow complete.")
    return summary


class NetworkResolutionError(Exception):
    """Permanent DNS resolution failure. Do not retry."""

def download(_, usable_id, url):
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


def summarize(_, filename):
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


def send_email(_, summary, email, promise_id):
    print(f"Summary: {summary}")
    print(
        f"Click to confirm: http://localhost:9000/confirm?confirm=true&promise_id={promise_id}"
    )
    print(
        f"Click to reject: http://localhost:9000/confirm?confirm=false&promise_id={promise_id}"
    )
    print(f"Email sent to {email} with summary and confirmation links.")
    return


def main():
    resonate.start()
    Event().wait()


if __name__ == "__main__":
    main()
