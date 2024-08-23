import unittest

from .digital_ocean_spaces import (
    DigitalOceanSpacesIntegrationTests,
    StorageInterfaceCreationTests,
)
from .main_tests import MainModuleTests
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

__all__ = [
    "ApacheTikaTextExtractorTest",
    "CreationDatabaseInterfaceFunctionTests",
    "DigitalOceanSpacesIntegrationTests",
    "FactoryMethodApacheTikaTest",
    "IndexInterfaceFactoryFunctionTests",
    "MainModuleTests",
    "OpensearchBasicTests",
    "OpensearchIntegrationTests",
    "PostgreSQLConnectionTests",
    "PostgreSQLTests",
    "StorageInterfaceCreationTests",
    "TextExtractionTaskTests",
    "unittest",
]
