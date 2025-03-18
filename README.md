# Website summarization application

This is an example website summarization application built with:

- Flask: webserver that handles HTTP requests
- Resonate: framework for distributed & concurrent applications
- Beautiful Soup: webscraper
- Ollama: LLM that summarizes content

This application uses [uv](https://docs.astral.sh/uv/) as the environment and package manager.

To install dependencies run:

```
uv sync
```

To run the HTTP gateway service:

```
uv run gateway
```

To run a summarization application node, in another terminal:

```
uv run app
```

To summarize a website:

```
curl -X POST http://localhost:5000/summarize -H "Content-Type: application/json" -d '{"url": "http://example.com", "email": "johndoe@example.com"}'
```
