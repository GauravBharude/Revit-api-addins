# -*- coding: utf-8 -*-

import os
from pyrevit import revit, DB
from ui import ExportUI

doc = revit.doc
uidoc = revit.uidoc

# ---------------- UI ---------------- #

ui = ExportUI()
ui.ShowDialog()

EXPORT_PATH = ui.export_path
EXPORT_MAP = ui.export_map
VIEW_NAME = ui.view_name

if not EXPORT_MAP:
    raise Exception("No NWC definitions provided")

if not EXPORT_PATH or not VIEW_NAME:
    raise Exception("Export cancelled or invalid input")

# ---------------- SETUP ---------------- #

if not os.path.exists(EXPORT_PATH):
    os.makedirs(EXPORT_PATH)

# ---------------- FIND 3D VIEW ---------------- #

view_3d = None
for v in DB.FilteredElementCollector(doc).OfClass(DB.View3D):
    if (
        not v.IsTemplate
        and v.ViewType == DB.ViewType.ThreeD
        and v.Name == VIEW_NAME
    ):
        view_3d = v
        break

if not view_3d:
    raise Exception("Selected 3D view not found")



# ---------------- WORKSETS ---------------- #

worksets = {}

if doc.IsWorkshared:
    worksets = {
        ws.Name: ws for ws in
        DB.FilteredWorksetCollector(doc)
        .OfKind(DB.WorksetKind.UserWorkset)
    }

# Save original visibility
original_visibility = {}
if worksets:
    original_visibility = {
        ws.Id: view_3d.GetWorksetVisibility(ws.Id)
        for ws in worksets.values()
    }

# ---------------- EXPORT LOOP ---------------- #

for nwc_name, visible_ws in EXPORT_MAP.items():

    if worksets:
        with revit.Transaction("Set Worksets - {}".format(nwc_name)):
            for ws in worksets.values():
                view_3d.SetWorksetVisibility(
                    ws.Id,
                    DB.WorksetVisibility.Visible
                    if ws.Name in visible_ws
                    else DB.WorksetVisibility.Hidden
                )

   

    opts = DB.NavisworksExportOptions()
    opts.ExportScope = DB.NavisworksExportScope.View
    opts.ViewId = view_3d.Id
    opts.ExportLinks = True
    opts.ExportElementIds = True
    opts.Coordinates = DB.NavisworksCoordinates.Shared

    doc.Export(EXPORT_PATH, nwc_name + ".nwc", opts)

# ---------------- RESTORE ---------------- #

if worksets:
    with revit.Transaction("Restore Workset Visibility"):
        for ws_id, vis in original_visibility.items():
            view_3d.SetWorksetVisibility(ws_id, vis)



print("NWC export completed successfully.")
