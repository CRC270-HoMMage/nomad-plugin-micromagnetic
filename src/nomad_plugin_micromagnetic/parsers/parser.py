from typing import TYPE_CHECKING

import numpy as np
from nomad.parsing.parser import MatchingParser

from nomad_plugin_micromagnetic.schema_packages.schema_package import (
    MicromagneticField,
    MicromagneticGeometry,
    MicromagneticSimulation,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger


class MumaxOVFParser(MatchingParser):
    """
    Parser for mumax OVF (OVF2 text) files.

    This implementation assumes OVF2 in ASCII (text) format, as typically produced
    by mumax3. Binary support can be added later by checking the header fields
    "datatype" etc.
    """

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] | None = None,
    ) -> None:
        logger.info('MumaxOVFParser.parse', mainfile=mainfile)

        # ----------------------------------------------------------------------
        # 1. Create the root micromagnetic simulation object
        # ----------------------------------------------------------------------
        simulation = MicromagneticSimulation()
        archive.data = simulation

        # ----------------------------------------------------------------------
        # 2. Read OVF header
        # ----------------------------------------------------------------------
        with open(mainfile, 'rb') as f:
            header_lines: list[str] = []

            while True:
                line = f.readline()
                if not line:
                    raise ValueError('Unexpected EOF while reading OVF header')

                line_str = line.decode('utf-8', errors='ignore').strip()

                # OVF: data section begins here
                if line_str.startswith('# Begin: Data'):
                    break

                header_lines.append(line_str)

            # Convert header "key: value" pairs into a dict with lowercase keys
            header: dict[str, str] = {}
            for line in header_lines:
                if ':' not in line:
                    continue
                # Typical form: "# xnodes: 128"
                raw = line.lstrip('#').strip()
                key, value = raw.split(':', 1)
                header[key.strip().lower()] = value.strip()

            try:
                nx = int(header['xnodes'])
                ny = int(header['ynodes'])
            except KeyError as exc:
                raise ValueError(f'Missing required OVF header key: {exc}') from exc

            nz = int(header.get('znodes', '1'))

            dx = float(header.get('xstepsize', '1.0'))
            dy = float(header.get('ystepsize', '1.0'))
            dz = float(header.get('zstepsize', '1.0'))

            n_cells = nx * ny * nz

            # ------------------------------------------------------------------
            # 3. Read magnetization data (Mx, My, Mz) as ASCII floats
            # ------------------------------------------------------------------
            data = []

            for _ in range(n_cells):
                line = f.readline()
                if not line:
                    raise ValueError('Unexpected EOF in OVF data block')
                parts = line.split()
                if len(parts) < 3:
                    # skip empty / malformed lines
                    continue
                mx, my, mz = map(float, parts[:3])
                data.append([mx, my, mz])

        m_array = np.asarray(data, dtype=float)
        if m_array.shape[0] != n_cells:
            logger.warning(
                'Number of magnetization vectors does not match header.',
                expected=n_cells,
                read=m_array.shape[0],
            )

        # ----------------------------------------------------------------------
        # 4. Fill geometry section
        # ----------------------------------------------------------------------
        geom = MicromagneticGeometry()
        geom.nx = nx
        geom.ny = ny
        geom.nz = nz
        geom.dx = dx
        geom.dy = dy
        geom.dz = dz
        simulation.geometry = geom

        # ----------------------------------------------------------------------
        # 5. Create one field snapshot subsection
        # ----------------------------------------------------------------------
        field = MicromagneticField()
        # Basic metadata; refine if you can get this from file name or header
        field.index = 0
        field.time = 0.0  # seconds; set properly if you have it
        field.B_ext = np.zeros(3)  # Tesla; set properly if available

        # Total number of cells (match the schema dimension)
        field.n_cells = n_cells
        field.nx = nx
        field.ny = ny

        # Full magnetisation field, shape (n_cells, 3)
        field.m = m_array

        # Compute a default Mz slice at z=0 for visualization.
        # Keep it as a 2D array (ny, nx) so Plotly can render it directly.
        try:
            field4d = m_array.reshape((nz, ny, nx, 3))  # (nz, ny, nx, 3)
            mz = field4d[0, :, :, 2]  # (ny, nx) at z = 0
            field.mz_slice = mz
        except Exception as exc:
            logger.warning('Failed to compute mz_slice', error=str(exc))

        # Attach the field snapshot to the simulation
        # For repeated subsections, NOMAD stores them in a list.
        simulation.fields = [field]
