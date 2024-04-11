from typing import Any, Dict, Iterable

from segmentation.base import AssociationSegmenter
from segmentation import segmenters


_segmenter_instances = {}


def get_segmenter(territory_id: str, territories: Iterable[Dict[str, Any]]) -> AssociationSegmenter:
    """
    Factory method to return a AssociationSegmenter

    Example
    -------
    >>> territory_id = "9999999"
    >>> territories = [
        {
            "id": "9999999",
            "territory_name": "Bairro do Limoeiro",
            "state_code": "ZZ",
            "state": "Limoeirolândia",
        }, {
            "id": "0000000",
            "territory_name": "Castelo Rá-Tim-Bum",
            "state_code": "SP",
            "state": "São Paulo",
        },
    ]
    >>> from segmentation import get_segmenter
    >>> segmenter = get_segmenter(territory_id, territories)
    >>> segments = segmenter.get_gazette_segments()

    Notes
    -----
    This method implements a factory method pattern.
    See: https://github.com/faif/python-patterns/blob/master/patterns/creational/factory.py
    """

    territory_to_segmenter_class = {
        "2700000": "ALAssociacaoMunicipiosSegmenter",
    }

    if territory_id not in _segmenter_instances:
        segmenter_class_name = territory_to_segmenter_class[territory_id]
        segmenter_class = getattr(segmenters, segmenter_class_name)
        _segmenter_instances[territory_id] = segmenter_class(territories)

    return _segmenter_instances[territory_id]
