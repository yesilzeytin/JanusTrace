"""
Entry point for the GUI version of JanusTrace.
"""
from trace_framework.ui.gui_app import JanusTraceApp

if __name__ == "__main__":
    app = JanusTraceApp()
    app.mainloop()
