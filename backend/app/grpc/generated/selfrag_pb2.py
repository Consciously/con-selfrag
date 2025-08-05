"""
Generated protobuf code for Selfrag gRPC services.
This is a placeholder file for Phase 2 - actual compilation will happen in Phase 3.
"""

# Placeholder classes for type safety
class HealthCheckRequest:
    def __init__(self, service: str = ""):
        self.service = service

class HealthCheckResponse:
    def __init__(self, status: str = "SERVING", message: str = ""):
        self.status = status
        self.message = message

class QueryRequest:
    def __init__(self, query: str = "", limit: int = 10, filters: dict = None, 
                 context: str = "", session_id: str = "", enable_reranking: bool = True):
        self.query = query
        self.limit = limit
        self.filters = filters or {}
        self.context = context
        self.session_id = session_id
        self.enable_reranking = enable_reranking

class QueryResponse:
    def __init__(self, query: str = "", context: str = "", results: list = None,
                 total_results: int = 0, query_time_ms: int = 0, 
                 reranked: bool = False, context_used: bool = False):
        self.query = query
        self.context = context
        self.results = results or []
        self.total_results = total_results
        self.query_time_ms = query_time_ms
        self.reranked = reranked
        self.context_used = context_used

class IngestRequest:
    def __init__(self, content: str = "", metadata: dict = None):
        self.content = content
        self.metadata = metadata or {}

class IngestResponse:
    def __init__(self, id: str = "", status: str = "", message: str = ""):
        self.id = id
        self.status = status
        self.message = message
