import gvm
from gvm.protocols.latest import Gmp
from gvm.transforms import EtreeTransform
from gvm.xml import pretty_print

connection =gvm.connections.TLSConnection(hostname='localhost', port=9390)
gmp = Gmp(connection)
gmp.authenticate('admin', 'admin')

# Retrieve current GMP version
version = gmp.get_version()

# Prints the XML in beautiful form
pretty_print(version)