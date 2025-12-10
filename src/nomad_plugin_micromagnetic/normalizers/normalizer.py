from typing import TYPE_CHECKING

import numpy as np
from nomad.normalizing import Normalizer

from nomad_plugin_micromagnetic.schema_packages.schema_package import (
    MicromagneticField,
    MicromagneticGeometry,
    MicromagneticSimulation,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


class MicromagneticNormalizer(Normalizer):
    """
    Normalizer for micromagnetic simulations.

    Responsibilities here:
    - reshape the magnetisation field if needed,
    - compute a default 2D Mz slice for visualization,
    - optionally compute simple derived quantities.
    """

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        # Always call parent normalize first
        super().normalize(archive, logger)

        data = getattr(archive, 'data', None)
        if not isinstance(data, MicromagneticSimulation):
            return

        geom: MicromagneticGeometry | None = getattr(data, 'geometry', None)
        if geom is None or geom.nx is None or geom.ny is None or geom.nz is None:
            logger.warning(
                'MicromagneticNormalizer: missing geometry (nx, ny, nz).',
            )
            return

        nx, ny, nz = geom.nx, geom.ny, geom.nz

        fields = getattr(data, 'fields', None)
        if not fields:
            logger.info('MicromagneticNormalizer: no field snapshots found.')
            return

        for field in fields:
            if not isinstance(field, MicromagneticField):
                continue

            m = getattr(field, 'm', None)
            if m is None:
                logger.warning('MicromagneticNormalizer: field.m is None, skipping.')
                continue

            m_arr = np.asarray(m, dtype=float)

            expected_cells = nx * ny * nz
            if m_arr.shape[0] != expected_cells or m_arr.shape[-1] != 3:
                logger.warning(
                    'MicromagneticNormalizer: unexpected m shape.',
                    shape=m_arr.shape,
                    expected_cells=expected_cells,
                )
                continue

            # Reshape to (nz, ny, nx, 3) assuming mumax/OVF ordering
            try:
                m_4d = m_arr.reshape((nz, ny, nx, 3))
            except ValueError as exc:
                logger.warning(
                    'MicromagneticNormalizer: failed to reshape m.', error=str(exc)
                )
                continue

            # Store dimensions for this field (must match mz_slice shape)
            field.nx = nx
            field.ny = ny
            field.n_cells = expected_cells

            # Compute Mz slice at z = 0, shape (ny, nx)
            try:
                mz = m_4d[0, :, :, 2]  # (ny, nx)
                field.mz_slice = mz  # schema expects ['ny', 'nx']
            except Exception as exc:
                logger.warning(
                    'MicromagneticNormalizer: failed to compute mz_slice.',
                    error=str(exc),
                )
                continue

            # Example of a simple derived quantity: average magnetisation vector
            try:
                m_avg = np.mean(m_4d.reshape(-1, 3), axis=0)
                # Only store if you've added a corresponding Quantity to the schema.
                # field.m_average = m_avg
            except Exception as exc:
                logger.warning(
                    'MicromagneticNormalizer: failed to compute average magnetisation.',
                    error=str(exc),
                )
