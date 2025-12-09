import numpy as np
from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import (
    MSection,
    Quantity,
    SchemaPackage,
    Section,
    SubSection,
)

# This is the container for all definitions in this schema package
m_package = SchemaPackage()


class MicromagneticGeometry(MSection):
    """
    Discretization / mesh geometry for a micromagnetic simulation.
    """

    m_def = Section(label='Micromagnetic geometry')

    nx = Quantity(
        type=int,
        description='Number of cells along x.',
    )
    ny = Quantity(
        type=int,
        description='Number of cells along y.',
    )
    nz = Quantity(
        type=int,
        description='Number of cells along z.',
    )

    dx = Quantity(
        type=float,
        unit='m',
        description='Cell size along x.',
    )
    dy = Quantity(
        type=float,
        unit='m',
        description='Cell size along y.',
    )
    dz = Quantity(
        type=float,
        unit='m',
        description='Cell size along z.',
    )


class MicromagneticField(PlotSection, MSection):
    """
    One magnetisation field snapshot (e.g. from a single OVF file).
    """

    m_def = Section(
        label='Micromagnetic field snapshot',
        a_plotly_express=[
            {
                # Use Plotly Express imshow on mz_slice
                'method': 'imshow',
                'img': '#mz_slice',  # quantity to plot (NOT 'z')
                'label': 'Mz slice (z = 0)',
                'open': True,
                'layout': {
                    'title': {'text': 'Mz slice (z = 0)'},
                    'xaxis': {'title': 'x index'},
                    'yaxis': {'title': 'y index'},
                },
            }
        ],
    )

    # Local copy of dimensions for this field; used for mz_slice shape.
    nx = Quantity(
        type=int,
        description='Number of cells along x for this field.',
    )
    ny = Quantity(
        type=int,
        description='Number of cells along y for this field.',
    )

    # Total number of cells in the grid; used as a symbolic dimension.
    n_cells = Quantity(
        type=int,
        description='Number of cells in the field grid (typically nx * ny * nz).',
    )

    index = Quantity(
        type=int,
        description='Index of this snapshot in a sequence (0, 1, 2, ...).',
    )

    time = Quantity(
        type=float,
        unit='s',
        description='Simulation time associated with this snapshot.',
    )

    B_ext = Quantity(
        type=float,
        shape=[3],
        unit='tesla',
        description='Applied external magnetic field vector for this snapshot.',
    )

    # Full magnetisation vector field on the grid, flattened.
    m = Quantity(
        type=np.float64,
        shape=['n_cells', 3],
        description='Magnetisation vector field (Mx, My, Mz) flattened over all cells.',
    )

    # Mz slice at z=0, as a 2D array (ny, nx) for plotting.
    mz_slice = Quantity(
        type=np.float64,
        shape=['ny', 'nx'],
        description='Mz component at z = 0, as a 2D array (ny, nx).',
    )


class MicromagneticSimulation(Schema):
    """
    Root section for a micromagnetic simulation entry.

    This is what will typically live in archive.data.
    """

    m_def = Section(label='Micromagnetic simulation')

    geometry = SubSection(
        sub_section=MicromagneticGeometry,
        description='Discretization and cell sizes used for the simulation.',
    )

    fields = SubSection(
        sub_section=MicromagneticField,
        repeats=True,
        description='Magnetisation field snapshots (e.g. OVF files).',
    )


# Finalize metainfo definitions in this package
m_package.__init_metainfo__()
