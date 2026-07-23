class GovExamAgentError(Exception):
    """Base class for project-specific exceptions."""

    def __init__(self, message: str, agent_type: str = "", details: dict | None = None):
        super().__init__(message)
        self.agent_type = agent_type
        self.details = details or {}


class LLMAPIError(GovExamAgentError):
    """LLM API failed because of timeout, network, quota, or provider error."""


class AgentExecutionError(GovExamAgentError):
    """Agent execution failed."""


class ToolExecutionError(GovExamAgentError):
    """Tool or MCP call failed."""


class MilvusConnectionError(GovExamAgentError):
    """Milvus is unavailable or query failed."""


class InvalidInputError(GovExamAgentError):
    """Input is invalid and retrying cannot fix it."""


class AuthenticationError(GovExamAgentError):
    """Authentication failed and retrying cannot fix it."""
