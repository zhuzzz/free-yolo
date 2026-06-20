"""Heuristic topic tagging from a resource's text. No ML needed for MVP."""

from __future__ import annotations

from .models import Resource

# topic -> keywords (lowercased, substring match)
_TOPIC_KEYWORDS = {
    "fundamentals": ["intro", "basics", "fundamental", "beginner", "getting started", "101"],
    "llm": ["llm", "large language model", "gpt", "transformer", "language model"],
    "prompting": ["prompt", "prompting", "few-shot", "chain of thought"],
    "rag": ["rag", "retrieval", "vector", "embedding", "semantic search"],
    "agents": ["agent", "agentic", "tool use", "function calling", "autonomous"],
    "fine-tuning": ["fine-tun", "finetun", "lora", "peft", "training"],
    "deep-learning": ["deep learning", "neural network", "backprop", "pytorch", "tensorflow"],
    "computer-vision": ["vision", "image", "diffusion", "stable diffusion", "cnn"],
    "nlp": ["nlp", "natural language", "tokeniz", "named entity"],
    "mlops": ["mlops", "deploy", "production", "serving", "monitoring"],
    "evals": ["eval", "benchmark", "evaluation", "red team"],
    "safety": ["safety", "alignment", "responsible ai", "ethics", "bias"],
    "ml-math": ["linear algebra", "probability", "statistics", "calculus", "math for"],
    "data": ["dataset", "data engineering", "feature", "pandas"],
}


def topics_for(text: str) -> list[str]:
    low = text.lower()
    hits = [topic for topic, kws in _TOPIC_KEYWORDS.items()
            if any(k in low for k in kws)]
    return hits


def enrich(r: Resource) -> Resource:
    """Fill in topics from title+description if none were provided."""
    if not r.topics:
        r.topics = topics_for(f"{r.title} {r.description}")
    return r
