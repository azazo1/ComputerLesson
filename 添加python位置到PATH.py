import sys
import os
os.system('setx PATH=%PATH%;{}'.format(';'.join(sys.path)))
