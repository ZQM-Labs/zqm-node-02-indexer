Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer"
WshShell.Run """C:\Users\zqmco\OneDrive\Desktop\zqm-node-02-indexer\.venv\Scripts\python.exe"" """ & _
    WshShell.CurrentDirectory & "\zqm_node_service_proxy.py""", 0, False
