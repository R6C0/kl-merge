r"""workdir.py   prints the work folder (tools\kl_port_check.workdir()); for build.bat --work / build_auto.bat --work."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import kl_port_check
print(kl_port_check.workdir())
