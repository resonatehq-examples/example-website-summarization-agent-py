# Website summarization application

This is an example website summarization application built with:

- Flask: webserver that handles HTTP requests
- Resonate: framework for distributed & concurrent applications
- Beautiful Soup: webscraper
- Ollama: LLM that summarizes content

This application uses [uv](https://docs.astral.sh/uv/) as the environment and package manager.

**Prerequisites:**

- Make sure you have [Ollama](https://ollama.com/) installed and running llama3.1
- Make sure you have a Google Chrome browser running.

**Running the application:**

When running this application locally, you will use 4 separate terminals, each representing its own process, representing a distributed application separated by a network.

Run a local Resonate Server:

```
brew install resonatehq/tap/resonate
resonate serve
```

In another terminal install dependencies:

```
uv sync
```

Run the HTTP gateway service:

```
uv run gateway
```

In another terminal run a summarization application node:

```
uv run app
```

From another terminal summarize a website:

```
curl -X POST http://localhost:5000/summarize -H "Content-Type: application/json" -d '{"url": "https://resonatehq.io", "email": "johndoe@example.com"}'
```

You will be prompted from the application node terminal to accept or reject the summarization.

- Accepting will complete the workflow.
- Rejecting will invoke another summarization attempt.
