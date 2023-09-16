from pony.orm import *
import sys
from datetime import *
from pathlib import Path


db = pony.orm.Database()

if "pytest" in sys.modules:
    db.bind(provider='sqlite', filename=':sharedmemory:')
else:
    db.bind(provider='sqlite', filename='db.lacosa', create_db=True)

