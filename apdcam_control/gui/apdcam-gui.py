#!/usr/bin/python3

import sys
import os
dir = os.path.dirname(__file__)
sys.path.append(dir + '/../../')
import apdcam_control

# def trace(frame, event, arg):
#     print("%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno))
#     return trace

# def test():
#     print("Line 8")
#     print("Line 9")

# sys.settrace(trace)

app = apdcam_control.gui.ApdcamGuiApp()
sys.exit(app.exec())

