from nomad.config.models.plugins import SchemaPackageEntryPoint


class MicromagneticSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        # Import here to avoid circular imports at import time
        from micromagnetic_test_plugin.schema_packages.schema_package import m_package

        return m_package


schema_package_entry_point = MicromagneticSchemaPackageEntryPoint(
    name='MicromagneticSchema',
    description='Schema for micromagnetic simulations (mumax OVF, etc.).',
)
