

bl_info = {
    "name": "Space Switcher Utility",
    "author": "BlenderBoi",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "Side Panel > Space Switcher Utilities",
    "description": "Generate Empties with Constraint and Bakes",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}


import mathutils

import bpy
from bpy_extras import anim_utils


context = bpy.context



def create_empty(name):
    empty = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(empty)

    
    return empty


def bake_action(obj, action, start, end, bake_settings):

    frames = [i for i in range(start, end)]
    obj_act = [[obj, action]]

    only_selected = bake_settings["only_selected"]
    do_pose= bake_settings["do_pose"]
    do_object= bake_settings["do_object"]
    do_visual_keying= bake_settings["do_visual_keying"]
    do_constraint_clear= bake_settings["do_constraint_clear"]
    do_parents_clear= bake_settings["do_parents_clear"]
    do_clean= bake_settings["do_clean"]


    baked_actions = anim_utils.bake_action_objects(
        obj_act,
        frames=frames,
        only_selected=only_selected,
        do_pose=do_pose,
        do_object=do_object,
        do_visual_keying=do_visual_keying,
        do_constraint_clear=do_constraint_clear,
        do_parents_clear=do_parents_clear,
        do_clean=do_clean,
    )
    
    baked_action = baked_actions[0]

    return baked_action




class SPACESWITCHERUTILS_OT_Clear_Space_Swithcer_Empties(bpy.types.Operator):
    """Clear Space Swithcer Empties"""
    bl_idname = "spaceswitchutils.clear_space_switcher_empties"
    bl_label = "Clear Space Switcher Empties"
    bl_options = {"REGISTER", "UNDO"}

    

    def execute(self, context):
        
        
        for object in context.view_layer.objects:
            if object.is_space_switcher_empties:
                bpy.data.objects.remove(object)

            


                
        
        
        return {'FINISHED'}


ENUM_Constraint_Type = [("COPY_LOCATION","Copy Location","Copy Location"),("COPY_ROTATION","Copy Rotation","Copy Rotation"),("CHILD_OF","Child Of","Child Of")]

class SPACESWITCHERUTILS_OT_Create_Space_Switcher_Empties(bpy.types.Operator):
    """Create Space Switcher Empties"""
    bl_idname = "spaceswitchutils.create_space_switcher_empties"
    bl_label = "Create Space Swithcer Empties from Selected Pose Bones"
    bl_options = {"REGISTER", "UNDO"}

    constraint_type: bpy.props.EnumProperty(items=ENUM_Constraint_Type, name="Consraint")
    preclear_empties: bpy.props.BoolProperty(default=True, name="Preclear Space Switcher Empties")
    start_frame: bpy.props.IntProperty(name="Start Frame")
    end_frame: bpy.props.IntProperty(name="End Frame")
    offset_frame: bpy.props.IntProperty(default=0, name="Offset Frame")
    #apply_empties: bpy.props.BoolProperty(default=False, name="Apply After Create")
    offset_child: bpy.props.FloatProperty(default=2, min=0.01, name="Empty Offset")
    constraint_bone_to_empty: bpy.props.BoolProperty(default=True, name="Constraint Bone to Empty")
    
    def invoke(self, context, event):
        
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        layout.prop(self, "constraint_type", expand=True)
        if self.constraint_type == "CHILD_OF":
            layout.prop(self, "offset_child")
        
        row = layout.row(align=True)
        row.prop(self, "start_frame")
        row.prop(self, "end_frame")
        layout.prop(self, "offset_frame")
        layout.separator()
        layout.prop(self, "preclear_empties")
        layout.prop(self, "constraint_bone_to_empty")
        #layout.prop(self, "apply_empties")

    
    
    @classmethod
    def poll(cls, context):
        if context.selected_pose_bones:
            if len(context.selected_pose_bones) > 0:
                return True

    def execute(self, context):
        
        if self.preclear_empties:
            bpy.ops.spaceswitchutils.clear_space_switcher_empties()
        
        bake_settings = {}

        bake_settings["only_selected"] = False
        bake_settings["do_pose"] = False
        bake_settings["do_object"] = True
        bake_settings["do_visual_keying"] = True
        bake_settings["do_constraint_clear"] = True
        bake_settings["do_parents_clear"] = False
        bake_settings["do_clean"] = False


        start_frame = self.start_frame
        end_frame = self.end_frame


        for pose_bone in context.selected_pose_bones:
            
            obj = pose_bone.id_data
            
            empty = create_empty(obj.name + "_" + pose_bone.name + "_Space_Switcher_Empties")
            empty.matrix_world = obj.matrix_world @ pose_bone.matrix 
            
            


            
            constraint = empty.constraints.new(self.constraint_type)
            if self.constraint_type == "CHILD_OF":




                constraint.inverse_matrix = empty.matrix_world.inverted()

                dir = mathutils.Vector((0, 1, 0)) * self.offset_child
            
                empty.matrix_basis @= mathutils.Matrix.Translation(dir)
 

                


            
            
            constraint.target = obj
            constraint.subtarget = pose_bone.name




            empty.select_set(True)
            
            empty.is_space_switcher_empties = True
            empty.empty_display_type = "ARROWS"
            empty.space_switcher_owner = obj
            empty.space_switcher_bone = pose_bone.name
            empty.space_switcher_type = self.constraint_type
            
            if empty.space_switcher_type == "CHILD_OF":
                empty.space_switcher_type = "DAMPED_TRACK"
                            

            
            action = bpy.data.actions.new(empty.name + "Temp_Action")
            action = bake_action(empty, action, start_frame, end_frame, bake_settings)
            


            anim_data = empty.animation_data_create()
            anim_data.action = action
            
            for fc in action.fcurves:
                
 
                fc.modifiers.new("CYCLES")
                for kf in fc.keyframe_points:
                    kf.co.x += self.offset_frame
            


            for fc in action.fcurves:
                if self.constraint_type == "COPY_LOCATION":
                    
                    if not fc.data_path == "location":
                        action.fcurves.remove(fc)
                        
                if self.constraint_type in ["COPY_ROTATION", "DAMPED_TRACK"]:

                    if not fc.data_path in ["rotation_euler", "rotation_axis_angle", "rotation_quaternion"]:
                        action.fcurves.remove(fc)
                


            constraint = pose_bone.constraints.new(empty.space_switcher_type)
            constraint.target = empty

            if empty.space_switcher_type == "COPY_ROTATION":
                constraint = empty.constraints.new("COPY_LOCATION")
                constraint.target = obj 
                constraint.subtarget = pose_bone.name


             
        #if self.apply_empties:
        #    bpy.ops.spaceswitchutils.apply_space_switcher_empties_to_pose_bones(selected=True)
            
        return {'FINISHED'}


#Damped Track
#Copy Location
#Copy Rotation


class SPACESWITCHERUTILS_OT_Apply_Space_Switcher_Empties(bpy.types.Operator):
    """Apply Space Swithcer Empties to Pose Bones"""
    bl_idname = "spaceswitchutils.apply_space_switcher_empties_to_pose_bones"
    bl_label = "Apply Space Swithcer Empties to Pose Bones"
    bl_options = {"REGISTER", "UNDO"}
    
    selected: bpy.props.BoolProperty(default=True)
    
    remove_empties: bpy.props.BoolProperty(default=True)
    start_frame: bpy.props.IntProperty(name="Start Frame")
    end_frame: bpy.props.IntProperty(name="End Frame")
    #offset_position: bpy.props.
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, "start_frame")
        row.prop(self, "end_frame")
        layout.prop(self, "remove_empties", text="Remove Empties After Apply")
    
    def invoke(self, context, event):
        
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end
        return context.window_manager.invoke_props_dialog(self)


    @classmethod
    def poll(cls, context):
        if context.mode in ["POSE", "OBJECT"]:
            return True

    def execute(self, context):
        
        bake_settings = {}

        bake_settings["only_selected"] = True
        bake_settings["do_pose"] = True
        bake_settings["do_object"] = False
        bake_settings["do_visual_keying"] = True
        bake_settings["do_constraint_clear"] = False
        bake_settings["do_parents_clear"] = False
        bake_settings["do_clean"] = False
        
        source_objects = []
        
        if self.selected:
            source_objects = context.selected_objects
            
        else:
            source_objects = context.view_layer.objects
        
        space_switcher_empties = [obj for obj in source_objects if obj.is_space_switcher_empties]
        


                
        for empty in space_switcher_empties:
            
            obj = empty.space_switcher_owner
            
            if obj:
                if empty.space_switcher_bone:
                    
                    for bone in obj.pose.bones:
                        bone.bone.select = False
                        
                    bone = obj.pose.bones.get(empty.space_switcher_bone)
                    if bone:
                        

                        for con in empty.constraints:
                            empty.constraints.remove(con)
                        
                        action = None
                        
                        if not obj.animation_data:
                            obj.animation_data_create()
                            
                        if obj.animation_data.action:
                            action = obj.animation_data.action
                            
                        else:
                            action = bpy.data.actions.new(obj.name + "_action")
                            
   
   
   
                        bone.bone.select = True
                        
                        if empty.animation_data:
                            if empty.animation_data.action:
        
                                start_frame = self.start_frame
                                end_frame = self.end_frame
                                action = bake_action(obj, obj.animation_data.action, start_frame, end_frame, bake_settings)
                        
                        
                        if self.remove_empties:
                            
                            bpy.data.objects.remove(empty)

                        for constraint in bone.constraints:
                            bone.constraints.remove(constraint)


                
        
        return {'FINISHED'}









class SPACESWITCHERUTILS_PT_Panel(bpy.types.Panel):
    """Create A Panels For Space Switcher Utility Tool"""
    bl_label = "Space Switcher Utilities"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Space Switcher Utilities"



    def draw(self, context):

        layout = self.layout
        
        row = layout.row(align=True)
        row.operator(
            SPACESWITCHERUTILS_OT_Create_Space_Switcher_Empties.bl_idname, text="Generate Empties", icon="ADD")
        row.operator(
            SPACESWITCHERUTILS_OT_Clear_Space_Swithcer_Empties.bl_idname, text="Clear All Empties", icon="TRASH")
            
        layout.label(text="Apply")
        
        row = layout.row(align=True)
        op = row.operator(
            SPACESWITCHERUTILS_OT_Apply_Space_Switcher_Empties.bl_idname, text="Selected", icon="CHECKMARK")
        op.selected = True
        op = row.operator(
            SPACESWITCHERUTILS_OT_Apply_Space_Switcher_Empties.bl_idname, text="All", icon="CHECKMARK")
        op.selected = False






classes = [SPACESWITCHERUTILS_PT_Panel, SPACESWITCHERUTILS_OT_Apply_Space_Switcher_Empties, SPACESWITCHERUTILS_OT_Clear_Space_Swithcer_Empties, SPACESWITCHERUTILS_OT_Create_Space_Switcher_Empties]



def register():

    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Object.is_space_switcher_empties = bpy.props.BoolProperty(default=False)
    bpy.types.Object.space_switcher_owner = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Object.space_switcher_bone = bpy.props.StringProperty()
    bpy.types.Object.space_switcher_type = bpy.props.StringProperty()
    

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
   

    del bpy.types.Object.is_space_switcher_empties
    del bpy.types.Object.space_switcher_owner
    del bpy.types.Object.space_switcher_bone
    del bpy.types.Object.space_switcher_type
    

    
if __name__ == "__main__":
    register()



