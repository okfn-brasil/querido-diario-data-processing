from typing import Any, Dict, Iterable, List, Union
from segmentation.base import GazetteSegment


class AssociationSegmenter:
    def __init__(self, territories: Iterable[Dict[str, Any]]):
        self.territories = territories

    def get_gazette_segments(self, *args, **kwargs) -> List[Union[GazetteSegment, Dict]]:
        """
        Returns a list of GazetteSegment
        """
        raise NotImplementedError

    def split_text_by_territory(self, *args, **kwargs) -> Union[Dict[str, str], List[str]]:
        """
        Segment a association text by territory
        and returns a list of text segments
        """
        raise NotImplementedError

    def build_segment(self, *args, **kwargs) -> GazetteSegment:
        """
        Returns a GazetteSegment
        """
        raise NotImplementedError

