"""
SPDX SBOM builder.
"""

class SPDXBuilder:
    """
    Builds SPDX 2.3 format SBOM.
    """
    def build(self, dependencies: list, metadata: dict) -> dict:
        """
        Build the complete SPDX SBOM.
        """
        # TODO: Implement builder
        return {}

    def _build_package(self, dep) -> dict:
        """
        Build a package entry for a dependency.
        """
        # TODO: Implement package builder
        return {}
