"""
Generated gRPC service code for Selfrag services.
This is a placeholder file for Phase 2 - actual compilation will happen in Phase 3.
"""

# Placeholder service stubs for type safety
class HealthStub:
    def __init__(self, channel):
        self.channel = channel
    
    def Check(self, request, timeout=None):
        # Placeholder implementation
        pass

class QueryStub:
    def __init__(self, channel):
        self.channel = channel
    
    def QueryContent(self, request, timeout=None):
        # Placeholder implementation
        pass

class IngestStub:
    def __init__(self, channel):
        self.channel = channel
    
    def IngestContent(self, request, timeout=None):
        # Placeholder implementation
        pass

# Placeholder servicer base classes
class HealthServicer:
    def Check(self, request, context):
        raise NotImplementedError()

class QueryServicer:
    def QueryContent(self, request, context):
        raise NotImplementedError()

class IngestServicer:
    def IngestContent(self, request, context):
        raise NotImplementedError()

# Placeholder service registration functions
def add_HealthServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass

def add_QueryServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass

def add_IngestServicer_to_server(servicer, server):
    # Placeholder - actual implementation in Phase 3
    pass
