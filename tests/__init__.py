import unittest

from .text_extraction_tests import (
    ApacheTikaTextExtractorTest,
    FactoryMethodApacheTikaTest,
)
from .digital_ocean_spaces import (
    DigitalOceanSpacesIntegrationTests,
    StorageInterfaceCreationTests,
)
from .postgresql import (
    PostgreSQLTests,
    PostgreSQLConnectionTests,
    CreationDatabaseInterfaceFunctionTests,
)
from .text_extraction_task_tests import TextExtractionTaskTests

from .main_tests import MainModuleTests

from .opensearch import (
    OpensearchBasicTests,
    IndexInterfaceFactoryFunctionTests,
    OpensearchIntegrationTests,
)
