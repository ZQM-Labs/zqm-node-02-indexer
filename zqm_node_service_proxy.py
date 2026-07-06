import sys
import os

try:
    import win32serviceutil
except ImportError:
    print("pywin32 required: .venv\\Scripts\\python.exe -m pip install pywin32", file=sys.stderr)
    sys.exit(1)

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Use the actual .py service module for pywin32 command-line handling
import zqm_node_service

win32serviceutil.HandleCommandLine(zqm_node_service.IndexerService)
