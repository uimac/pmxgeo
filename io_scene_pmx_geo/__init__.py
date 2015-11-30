# author: tori31001 at gmail.com
# website: http://pmxgeo.render.jp/

bl_info = {
    "name": "PmxGeoExport",
    "author": "Kazuma Hatta",
    "version": (0, 0, 3),
    "blender": (2, 7, 3),
    "location": "File > Import/Export > PmxGeo",
    "description": "Export pmx geometry cache",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Export"}
    
if "bpy" in locals():
    import imp
    if "export_pmx_geo" in locals():
        imp.reload(export_pmx_geo)

import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       EnumProperty,
                       )

from bpy_extras.io_utils import (ExportHelper)

class PmxGeoExportOperator(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.pmx_geo"
    bl_label = "Pmx Geo Exporter(.pmx + .vmd)"
    
    filename_ext = "."
    use_filter_folder = True
        
    model_base_name = StringProperty(\
        name="model base name",\
        description="model base name (ascii)",\
        default="pmxgeo",\
        )

    only_selected = BoolProperty(\
        name="only selected",\
        description="export only selected objects",\
        default=True,\
        )

    start_frame = IntProperty(\
        name="start frame",\
        description="start frame number",\
        default=0,\
        )

    end_frame = IntProperty(\
        name="end frame",\
        description="end frame number",\
        default=0,\
        )

    def execute(self, context):
        import os, sys
        cmd_folder = os.path.dirname(os.path.abspath(__file__))
        if cmd_folder not in sys.path:
            sys.path.insert(0, cmd_folder)
        import export_pmx_geo

        userpath = os.path.dirname(self.properties.filepath)
        if not os.path.exists(userpath):
            msg = "Please select exists directory\n"
            self.report({'WARNING'}, msg)

        export_pmx_geo.export_pmx_geo(\
                userpath, \
                self.model_base_name, \
                bpy.context, \
                self.only_selected,\
                self.start_frame,\
                self.end_frame)

        return {'FINISHED'}

    def invoke(self, context, event):
        import os
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "model_base_name")
        row = layout.row(align=True)
        row.prop(self, "only_selected")
        row = layout.row(align=True)
        row.prop(self, "start_frame")
        row = layout.row(align=True)
        row.prop(self, "end_frame")

#
# Registration
#
def menu_func_export(self, context):
    self.layout.operator(PmxGeoExportOperator.bl_idname, text="Pmx Geo (.pmx + .vmd)")
    
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    
if __name__ == "__main__":
    register()
