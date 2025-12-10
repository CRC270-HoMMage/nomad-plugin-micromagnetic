from nomad.config.models.plugins import NormalizerEntryPoint


class MicromagneticNormalizerEntryPoint(NormalizerEntryPoint):
    """
    Entry point for the micromagnetic normalizer.

    No configurable parameters for now; add Pydantic fields here if you ever
    want to make its behavior configurable.
    """

    def load(self):
        from nomad_plugin_micromagnetic.normalizers.normalizer import (
            MicromagneticNormalizer,
        )

        return MicromagneticNormalizer(**self.model_dump())


normalizer_entry_point = MicromagneticNormalizerEntryPoint(
    name='MicromagneticNormalizer',
    description='Compute derived quantities for micromagnetic simulations (e.g. Mz slices).',
)
