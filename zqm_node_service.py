"""
ZQM Node-02 Indexer Windows Service/daemon helper

Launch methods, in order of stability:
1. service-install.bat + service-ctl.bat: standard Windows service via sc.exe + python
2. service-debug-launch.vbs: silent manual launch via raw python.exe
3. start.bat: console foreground run
"""
import os
import sys
import time
import traceback
import win32event
import win32service
import win32serviceutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SITE_PACKAGES = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")
if os.path.isdir(SITE_PACKAGES) and SITE_PACKAGES not in sys.path:
    sys.path.insert(0, SITE_PACKAGES)

# Service-scoped logs outside OneDrive paths.
PROGRAM_DATA = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
ZQM_SERVICE_DIR = os.path.join(PROGRAM_DATA, "ZQM-Node-02-Indexer")
os.makedirs(ZQM_SERVICE_DIR, exist_ok=True)
START_LOG = os.path.join(ZQM_SERVICE_DIR, "service_startup.log")
STOP_LOG = os.path.join(ZQM_SERVICE_DIR, "service_shutdown.log")


def _log(path, message):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except Exception:
        pass


class IndexerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZQM-Node-02-Indexer"
    _svc_display_name_ = "ZQM Node-02 Workstation File Indexer"
    _svc_description_ = (
        "Flask + Waitress API for local file search index. "
        "Web UI at http://127.0.0.1:5000."
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        try:
            _log(START_LOG, f"service svc_name={self._svc_name_}")
            _log(START_LOG, f"BASE_DIR={BASE_DIR}")
            _log(START_LOG, f"SITE_PACKAGES={SITE_PACKAGES}")
            _log(START_LOG, f"sys.executable={sys.executable}")
            _log(START_LOG, f"sys.version={sys.version}")
            _log(START_LOG, "pre import app")
            import app as indexer_app  # noqa: E402
            _log(START_LOG, "post import app")
            from waitress.server import create_server  # noqa: E402
            _log(START_LOG, "post import waitress")

            application = indexer_app.app
            port = int(os.environ.get("PORT", "5000"))
            server = create_server(application, host="127.0.0.1", port=port)
            _log(START_LOG, f"waitress listening on 127.0.0.1:{port} pid={os.getpid()}")

            timeout_ms = 250
            while True:
                if win32event.WaitForSingleObject(self.hWaitStop, timeout_ms) == win32event.WAIT_OBJECT_0:
                    break
                try:
                    server.run()
                except Exception:
                    break
        except Exception as exc:
            _log(START_LOG, f"run failed: {exc}\n{traceback.format_exc()}")
        finally:
            _log(STOP_LOG, "service run end")

    def SvcDoStop(self):
        _log(STOP_LOG, "service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1].lower() in ("remove", "delete"):
        pass
    win32serviceutil.HandleCommandLine(IndexerService)
