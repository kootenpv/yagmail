import sh
import re

commit_count = sh.git('rev-list', ['--all']).count('\n')

with open('setup.py') as f:
    setup = f.read()

setup = re.sub("MICRO_VERSION = '[0-9]+'", "MICRO_VERSION = '{}'".format(commit_count), setup)
    
with open('setup.py', 'w') as f:
    f.write(setup)    

print(sh.python('setup.py', ['sdist', 'upload']))
