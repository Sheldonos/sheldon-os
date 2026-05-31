"""
API Gateway
Main API gateway implementation
"""

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


class APIGateway:  # pylint: disable=too-few-public-methods
    """
    API Gateway for Sheldon OS
    Provides REST and GraphQL endpoints
    """

    def __init__(self):
        self.app = FastAPI(
            title="Sheldon OS API",
            description="Agentic Operating System API",
            version="1.0.0",
        )
        self._setup_middleware()
        self._setup_routes()
        logger.info("API Gateway initialized")

    def _setup_middleware(self):
        """Setup middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "Sheldon OS API", "version": "1.0.0"}

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @self.app.get("/api/v1/agents")
        async def list_agents():
            return {"agents": []}

        @self.app.post("/api/v1/agents")
        async def create_agent(request: Request):
            await request.json()
            return {"agent_id": "mock_id", "status": "created"}

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API gateway"""
        uvicorn.run(self.app, host=host, port=port)
