from resonate import Resonate, Context, DurablePromise
from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Event
import ollama
import os


# Initialize Resonate and connect to remote storage and a task source
resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    task_source=Poller(url="http://localhost:8002", group="summarization-nodes"),
)


@resonate.register
def downloadAndSummarize(ctx: Context, url: str, clean_url: str, email: str):
    print("Downloading and summarizing content from", url)
    # Download the content from the URL
    filename = yield ctx.lfc(download, url, clean_url).options(durable=False)
    while True:
        # Summarize the content
        summary = yield ctx.lfc(summarize, url, filename)
        # Create a promise to confirm the summary
        promise = yield ctx.rfi(DurablePromise())
        # Send an email with the summary and promise ID
        yield ctx.lfc(send_email, summary, email, promise.id)
        # Wait for the summary to be accepted or rejected
        print("Waiting on confirmation")
        confirmed = yield promise

        if confirmed:
            break

    print("Summarization accepted and completed")
    return


def download(_: Context, url: str, clean_url: str):
    filename = f"{clean_url}.txt"

    # Check if the file already exists
    if os.path.exists(filename):
        print(f"File {filename} already exists. Skipping download.")
        return filename

    print(f"Downloading data from {url}")
    try:
        driver = webdriver.Chrome()
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        content = soup.get_text()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        driver.quit()
        print(f"Content saved to {filename}")
        return filename
    except Exception as e:
        print(f"Download failed: {e}")
        raise Exception(f"Failed to download data: {e}")


def summarize(_: Context, url: str, filename: str):
    print(f"Summarizing content from {url}")
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
        print(f"Summarization failed: {e}")
        raise Exception(f"Failed to summarize content: {e}")


def send_email(_: Context, summary: str, email: str, promise_id: str):
    print(f"Summary: {summary}")
    print(
        f"Click to confirm: http://localhost:5000/confirm?confirm=true&promise_id={promise_id}"
    )
    print(
        f"Click to reject: http://localhost:5000/confirm?confirm=false&promise_id={promise_id}"
    )
    print(f"Email sent successfully to {email}")
    return


def main():
    print("Summarization application node running")
    Event().wait()


if __name__ == "__main__":
    main()
