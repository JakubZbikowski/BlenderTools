import bpy
import bmesh

def calc_object_volume(obj):
	if obj.type != 'MESH':
		return None
	bm = bmesh.new()
	mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
	bm.from_mesh(mesh)
	bm.transform(obj.matrix_world)
	volume = bm.calc_volume()
	bm.free()
	obj.to_mesh_clear()
	return volume

class VolumeSearchItem(bpy.types.PropertyGroup):
	name: bpy.props.StringProperty()
	volume: bpy.props.FloatProperty()

class VolumeSearchProperties(bpy.types.PropertyGroup):
	volume_threshold: bpy.props.FloatProperty(
		name="Volume threshold",
		default=1.0,
		min=0.0,
		description="Search objects with volume smaller than threshold"
	)
	results: bpy.props.CollectionProperty(type=VolumeSearchItem)
	active_index: bpy.props.IntProperty()

class OBJECT_OT_SearchSmallObjects(bpy.types.Operator):
	bl_idname = "object.search_small_objects"
	bl_label = "Search"

	def execute(self, context):
		props = context.scene.volume_search_props
		threshold = props.volume_threshold

		selected_objects = context.selected_objects
		bpy.ops.object.select_all(action='DESELECT')
		
		objects_to_add = []
		props.results.clear()
		props.active_index = 0
		for obj in selected_objects:
			vol = calc_object_volume(obj)
			if vol is not None and vol < threshold:
				item = {"name": obj.name, "volume": vol}
				objects_to_add.append(item)

		objects_to_add.sort(key=lambda x: x['volume'])

		for item in objects_to_add:
			new_item = props.results.add()
			new_item.name = item['name']
			new_item.volume = item['volume']

		if not props.results:
			self.report({'INFO'}, "Didn't find objects smaller than threshold.")
		return {'FINISHED'}

class OBJECT_OT_SelectAllFromList(bpy.types.Operator):
	bl_idname = "object.select_all_from_list"
	bl_label = "Select all from list"
	
	def execute(self, context):
		props = context.scene.volume_search_props
		bpy.ops.object.select_all(action='DESELECT')
		for item in props.results:
			obj = bpy.data.objects.get(item.name)
			if obj:
				obj.select_set(True)
		return {'FINISHED'}

class VolumeSearchListUI(bpy.types.UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		obj = bpy.data.objects.get(item.name)
		if obj:
			vol_str = f"{item.volume:.4f}"
			label = f"{item.name} — {vol_str}"
			op = layout.operator("object.direct_select", text=label, emboss=False, icon="MESH_CUBE")
			op.obj_name = item.name

class OBJECT_OT_DirectSelect(bpy.types.Operator):
	bl_idname = "object.direct_select"
	bl_label = "Zaznacz obiekt z listy"

	obj_name: bpy.props.StringProperty()

	def execute(self, context):
		obj = bpy.data.objects.get(self.obj_name)
		if obj:
			bpy.ops.object.select_all(action='DESELECT')
			obj.select_set(True)
			context.view_layer.objects.active = obj
		return {'FINISHED'}


class VIEW3D_PT_VolumeSearchPanel(bpy.types.Panel):
	bl_label = "Search by volume"
	bl_idname = "VIEW3D_PT_volume_search"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Objects tools"

	def draw(self, context):
		layout = self.layout
		props = context.scene.volume_search_props

		layout.prop(props, "volume_threshold")
		layout.operator("object.search_small_objects", icon="VIEWZOOM")

		if props.results:
			layout.label(text="Found objects:")
			layout.template_list("VolumeSearchListUI", "", props, "results", props, "active_index", rows=6)
			layout.operator("object.select_all_from_list", text="Select all", icon="RESTRICT_SELECT_OFF")


classes = (
	VolumeSearchItem,
	VolumeSearchProperties,
	OBJECT_OT_SearchSmallObjects,
	OBJECT_OT_SelectAllFromList,
	OBJECT_OT_DirectSelect,
	VolumeSearchListUI,
	VIEW3D_PT_VolumeSearchPanel,
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Scene.volume_search_props = bpy.props.PointerProperty(type=VolumeSearchProperties)

def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.volume_search_props

if __name__ == "__main__":
	register()
