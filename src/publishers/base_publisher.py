from abc import ABC, abstractmethod

class BasePublisherAdapter(ABC):
    """
    分发终点战术接口 (Outbound Subprocess Gateway)
    
    This isolates the fragile execution of 3rd-party distribution (like OpenCLI XHS, 
    or a weird Node JS Bilibili plugin). If these fail, we catch them here without 
    blowing up the entire processing pipeline.
    """
    
    @abstractmethod
    def push(self, content: str, title: str, media_paths: list[str] = []) -> bool:
        pass
