from abc import ABC, abstractmethod
from typing import List
from core.schemas import RawContentEvent

class BaseSourceAdapter(ABC):
    """
    基础信息源拦截战术接口 (Abstract Inbound Interface).
    
    Any future GitHub custom data scrapers (be it written in Node, Rust, or Go) 
    should be wrapped behind a child Python class extending this base. The class must 
    use `subprocess.run()` internal logic and map the raw JSON stdout directly 
    into a List of `RawContentEvent`.
    """
    
    @abstractmethod
    def fetch(self, limit: int = 10) -> List[RawContentEvent]:
        """
        Obligatory entrypoint execution method executing the scrape sequence.
        Returns a strongly typed list of RawContentEvents dropping directly into the DataBus.
        """
        pass
