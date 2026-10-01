# Week 4 – Custom MCP Server

A small MCP server built with `FastMCP` (Python MCP SDK 1.x). It exposes three tools over the `stdio` transport:

| Tool | Purpose | Example arguments |
|---|---|---|
| `lookup_country` | Data lookup from an in-memory dataset | `{"name": "Japan"}` |
| `calculate` | Safe arithmetic evaluator (no `eval`) | `{"expression": "(3 + 4) * 2 ** 3", "precision": 2}` |
| `analyze_text` | Text stats or transformations | `{"text": "Hello MCP World", "operation": "slugify"}` |

## Setup

```bash
cd Week4-MCP_Server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Test with MCP Inspector

Requires Node.js 18+. Run from the project root with the venv active:

```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```

Open the URL the command prints (it includes an auth token), click **Connect**, then use **Tools → List Tools** and run each tool.

Alternative (uses the `mcp` CLI bundled via `mcp[cli]`):

```bash
mcp dev server.py
```
