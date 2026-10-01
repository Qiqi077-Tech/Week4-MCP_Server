"""Week 4 homework: a small MCP server exposing three example tools over stdio.

Tools:
  - lookup_country:  data lookup from an in-memory dataset
  - calculate:       safe arithmetic expression evaluator
  - analyze_text:    text statistics and transformations
"""

import ast
import operator
import re
from collections import Counter
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("week4-demo-server")


# ---------------------------------------------------------------------------
# Tool 1: data lookup
# ---------------------------------------------------------------------------

COUNTRIES: dict[str, dict] = {
    "japan": {"capital": "Tokyo", "population_millions": 124.5, "currency": "JPY", "continent": "Asia"},
    "france": {"capital": "Paris", "population_millions": 68.2, "currency": "EUR", "continent": "Europe"},
    "brazil": {"capital": "Brasília", "population_millions": 203.1, "currency": "BRL", "continent": "South America"},
    "canada": {"capital": "Ottawa", "population_millions": 40.1, "currency": "CAD", "continent": "North America"},
    "kenya": {"capital": "Nairobi", "population_millions": 55.1, "currency": "KES", "continent": "Africa"},
    "australia": {"capital": "Canberra", "population_millions": 26.6, "currency": "AUD", "continent": "Oceania"},
}


@mcp.tool()
def lookup_country(
    name: Annotated[str, Field(description="Country name to look up, case-insensitive (e.g. 'Japan').")],
) -> dict:
    """Look up basic facts (capital, population, currency, continent) about a country.

    Returns the country's record, or an error with the list of available countries
    if the name is not in the dataset.
    """
    record = COUNTRIES.get(name.strip().lower())
    if record is None:
        return {"error": f"Unknown country '{name}'.", "available": sorted(c.title() for c in COUNTRIES)}
    return {"country": name.strip().title(), **record}


# ---------------------------------------------------------------------------
# Tool 2: calculator
# ---------------------------------------------------------------------------

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large.")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


@mcp.tool()
def calculate(
    expression: Annotated[
        str,
        Field(description="Arithmetic expression using numbers, parentheses and + - * / // % ** (e.g. '(3 + 4) * 2 ** 3')."),
    ],
    precision: Annotated[
        int,
        Field(description="Number of decimal places to round the result to.", ge=0, le=15),
    ] = 6,
) -> dict:
    """Safely evaluate an arithmetic expression and return the numeric result.

    Only numeric literals and arithmetic operators are allowed; names, function
    calls and attribute access are rejected, so no arbitrary code is executed.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
    except ZeroDivisionError:
        return {"expression": expression, "error": "Division by zero."}
    except (SyntaxError, ValueError) as exc:
        return {"expression": expression, "error": str(exc)}
    return {"expression": expression, "result": round(result, precision)}


# ---------------------------------------------------------------------------
# Tool 3: text processing
# ---------------------------------------------------------------------------

@mcp.tool()
def analyze_text(
    text: Annotated[str, Field(description="The input text to analyze or transform.")],
    operation: Annotated[
        Literal["stats", "uppercase", "lowercase", "title", "reverse", "slugify"],
        Field(description="'stats' returns word/character counts and top words; the others return the transformed text."),
    ] = "stats",
    top_n: Annotated[
        int,
        Field(description="For 'stats': how many of the most frequent words to return.", ge=1, le=50),
    ] = 5,
) -> dict:
    """Compute statistics about a piece of text or apply a simple transformation to it."""
    if operation == "stats":
        words = re.findall(r"[A-Za-z0-9']+", text.lower())
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        return {
            "characters": len(text),
            "characters_no_spaces": len(re.sub(r"\s", "", text)),
            "words": len(words),
            "sentences": len(sentences),
            "unique_words": len(set(words)),
            "top_words": Counter(words).most_common(top_n),
        }
    transforms = {
        "uppercase": str.upper,
        "lowercase": str.lower,
        "title": str.title,
        "reverse": lambda s: s[::-1],
        "slugify": lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-"),
    }
    return {"operation": operation, "result": transforms[operation](text)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
