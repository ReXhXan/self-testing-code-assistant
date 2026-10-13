"""Optional HTTP API (pip install -r requirements-api.txt; uvicorn assistant.api:app)."""
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from .agent import SelfTestingAgent
from .config import get_settings
from .llm import LLM, get_llm


class SolveRequest(BaseModel):
    task: str = Field(..., min_length=3, max_length=8000)
    tests: str | None = None
    max_iterations: int | None = Field(None, ge=1, le=10)


def create_app(llm: LLM | None = None) -> FastAPI:
    s = get_settings()
    app = FastAPI(title="Self-Testing Code Assistant", version="1.0.0")
    model = llm or get_llm(s)

    @app.get("/health")
    def health():
        return {"status": "ok", "llm": s.llm_provider}

    @app.post("/solve")
    async def solve(req: SolveRequest):
        agent = SelfTestingAgent(model, req.max_iterations or s.max_iterations,
                                 s.sandbox_timeout_s, s.sandbox_memory_mb)
        res = await run_in_threadpool(agent.run, req.task, req.tests)
        return res.to_dict()

    return app


app = create_app()
