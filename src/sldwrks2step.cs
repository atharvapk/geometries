import win32com.client
import os

# Connects to the local SolidWorks seat (no extra license cost)
sw_app = win32com.client.Dispatch("SldWorks.Application")
sw_app.Visible = False

doc_path = os.path.abspath("bracket.sldprt")
step_path = os.path.abspath("bracket.step")

# Open silently
doc = sw_app.OpenDoc6(doc_path, 1, 1, "", 0, 0) # 1 = swDocPART, 1 = Silent

# Set AP242 export preference
sw_app.SetUserPreferenceIntegerValue(87, 242) # swStepExportPreference

# Export to STEP
doc.Extension.SaveAs3(step_path, 0, 1, None, None, 0, 0)
sw_app.CloseDoc(doc_path)