import sys
sys.path (0, '/opt/kuwaibaPyhtonMicroService/')

activate_this = '/opt/kuwaibaPyhtonMicroService/pythonApi/bin/activate_this.py'

with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from app import app as application