import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

from verify_compatibility_support import jar_contents

spec = importlib.util.spec_from_file_location('jar_verifier', Path(__file__).with_name('verify-jar.py'))
jar_verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jar_verifier)


class CommonJarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'gradle.properties').write_text('carpet_version=1.4.112\ntick_version=1.1.0\n')
        self.jar = self.root / 'build/libs/neoforge-carpet-1.4.112-tick-1.1.0.jar'
        self.jar.parent.mkdir(parents=True)

    def fixture(self, version_range, version='1.4.112-tick-1.1.0'):
        with zipfile.ZipFile(self.jar, 'w') as jar:
            jar.writestr('dev/clark/carpet_tick/compat/CarpetConflictGuard.class', b'fixture')
            jar.writestr('neoforge_carpet_tick.refmap.json', '{}')
            jar.writestr('META-INF/mods.toml', f'''[[mods]]
modId="neoforge_carpet_tick"
version="{version}"
[[dependencies.neoforge_carpet_tick]]
modId="forge"
mandatory=true
versionRange="{version_range}"
''')

    def test_common_range_is_accepted(self):
        self.fixture('[47.1.5,47.2),[47.4.0,47.5)')
        jar_verifier.verify(self.root)

    def test_single_loader_ranges_are_rejected(self):
        for version_range in ('[47.1.106,47.2)', '[47.4.0,47.5)', '[47.1.5,47.5)'):
            with self.subTest(version_range=version_range):
                self.fixture(version_range)
                with self.assertRaisesRegex(AssertionError, 'Common loader range'):
                    jar_verifier.verify(self.root)

    def test_version_mismatch_is_rejected(self):
        self.fixture('[47.1.5,47.2),[47.4.0,47.5)', '1.4.112-tick-1.0.1')
        with self.assertRaisesRegex(AssertionError, 'Metadata version'):
            jar_verifier.verify(self.root)

    def test_content_comparison_detects_bytecode_changes(self):
        self.fixture('[47.1.5,47.2),[47.4.0,47.5)')
        original = jar_contents(self.jar)
        with zipfile.ZipFile(self.jar, 'a') as jar:
            jar.writestr('dev/clark/carpet_tick/Extra.class', b'different runtime')
        self.assertNotEqual(original, jar_contents(self.jar))


if __name__ == '__main__':
    unittest.main()
