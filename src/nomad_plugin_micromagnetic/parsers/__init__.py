from nomad.config.models.plugins import ParserEntryPoint


class MumaxOVFParserEntryPoint(ParserEntryPoint):
    """
    Entry point for the mumax OVF parser.
    """

    def load(self):
        # Import here to avoid circular imports
        from micromagnetic_test_plugin.parsers.parser import MumaxOVFParser

        # You can pass configuration options via **self.model_dump() if you add
        # custom fields to this entry point. For now, we don't need any.
        return MumaxOVFParser(**self.model_dump())


parser_entry_point = MumaxOVFParserEntryPoint(
    name='MumaxOVFParser',
    description='Parser for micromagnetic OVF files from mumax.',
    mainfile_name_re=r'.*\.ovf$',  # match .ovf files
)
