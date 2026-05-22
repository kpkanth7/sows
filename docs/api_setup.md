# API Setup

## GitHub

Set `GITHUB_TOKEN` for better search quota. A fine-grained token with public repository read access is enough.

## Hacker News

No key is required.

## Stack Exchange

Set `STACKEXCHANGE_KEY` if you want higher quota. The app can run without it.

## arXiv

No key is required for normal use.

## Product Hunt

Set `PRODUCTHUNT_ACCESS_TOKEN`. Without it, the Product Hunt ingestor returns an empty list and the rest of the pipeline keeps running.

## GDELT

No key is required for the open document API.

## LLM Provider

The project starts with `LLM_PROVIDER=local`, a deterministic provider-agnostic fallback. Keep `backend/app/services/llm_service.py` as the swap point for Qwen, Mistral Small, or another hosted provider.
