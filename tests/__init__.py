import unittest

from .digital_ocean_spaces import (
    DigitalOceanSpacesIntegrationTests,
    StorageInterfaceCreationTests,
)
from .list_gazettes_pagination_tests import (
    GazettesListingPaginationTests,
    GazettesListingRegressionTests,
)
from .main_tests import MainModuleTests
from .metrics_tests import GazetteProcessingMetricsTests, PushgatewayTests
from .opensearch import (
    IndexInterfaceFactoryFunctionTests,
    OpensearchBasicTests,
    OpensearchIntegrationTests,
)
from .postgresql import (
    CreationDatabaseInterfaceFunctionTests,
    PostgreSQLConnectionTests,
    PostgreSQLTests,
)
from .text_extraction_task_tests import TextExtractionTaskTests
from .text_extraction_tests import (
    ApacheTikaTextExtractorTest,
    FactoryMethodApacheTikaTest,
)
from .work_queue_tests import ThemesFromQueueTests, WorkQueueTaskTests

__all__ = [
    "ApacheTikaTextExtractorTest",
    "CreationDatabaseInterfaceFunctionTests",
    "DigitalOceanSpacesIntegrationTests",
    "FactoryMethodApacheTikaTest",
    "GazettesListingPaginationTests",
    "GazettesListingRegressionTests",
    "IndexInterfaceFactoryFunctionTests",
    "GazetteProcessingMetricsTests",
    "MainModuleTests",
    "OpensearchBasicTests",
    "OpensearchIntegrationTests",
    "PostgreSQLConnectionTests",
    "PostgreSQLTests",
    "PushgatewayTests",
    "StorageInterfaceCreationTests",
    "TextExtractionTaskTests",
    "ThemesFromQueueTests",
    "WorkQueueTaskTests",
    "unittest",
]
