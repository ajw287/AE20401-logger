import sys
import os

import tkinter as tk
import pytest

# Add the main directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ae20401Logger

class TestMainFunction:
    """ A minimal test that the function runs
    """
    def test_main_runs(self, monkeypatch):
        # Mock the mainloop function to prevent the test from getting stuck
        def mock_mainloop(self):
            pass

        # Use monkeypatch to replace mainloop with our mock_mainloop
        monkeypatch.setattr(tk.Tk, "mainloop", mock_mainloop)

        try:
            #with pytest.raises(SystemExit):
            ae20401Logger.main()
        except Exception as e:
            assert False, f"main function raised an exception: {e}"
