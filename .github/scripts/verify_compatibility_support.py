"""Hash uncompressed JAR entries; ZIP timestamps are not runtime differences."""
import hashlib
import zipfile


def jar_contents(path):
    with zipfile.ZipFile(path) as jar:
        return {name: hashlib.sha256(jar.read(name)).hexdigest()
                for name in jar.namelist() if not name.endswith('/')}
