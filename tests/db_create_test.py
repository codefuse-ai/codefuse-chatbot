import os, sys


src_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
sys.path.append(src_dir)


from coagent.orm import create_tables

create_tables()