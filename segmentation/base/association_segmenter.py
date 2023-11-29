from typing import Union, Dict, List
from segmentation.base import GazetteSegment


class AssociationSegmenter:
    def __init__(self, association_gazette: str, territory_to_data: Dict):
        self.association_gazette = association_gazette
        self.territory_to_data = territory_to_data

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

