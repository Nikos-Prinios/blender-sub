bl_info = {
	"name": "Blend-Sub",
	"author": "Nicolas Priniotakis (Nikos)",
	"version": (0,0,1,0),
	"blender": (2, 7, 4, 0),
	"api": 44539,
	"category": "Sequencer",
	"location": "Sequencer > UI > Blend-Sub",
	"description": "Subtitling system for the Video Sequence Editor",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",}

''' ------------------------------------------------------------------------------'''
'''                      IMPORT / PROPERTIES / VARIABLES                          '''
''' ------------------------------------------------------------------------------'''
import bpy, random
from bpy.app.handlers import persistent

bpy.types.Scene.snap = bpy.props.BoolProperty(name="Snap",description="Snap markers to the highest sound level around",default = False)
bpy.types.Scene.sub_file = bpy.props.StringProperty(name="Caption_file_name")
bpy.types.Scene.sub_file = 'English'

global strips, adding_sub, current_strip, framerate

framerate = 24 #bpy.context.scene.render.fps
adding_sub = False

''' ------------------------------------------------------------------------------'''
'''                                 FUNCTIONS                                     '''
''' ------------------------------------------------------------------------------'''

def strip_list():
	global strips, List
	strips = []
	update_caption_list()
	for s in bpy.context.scene.sequence_editor.sequences_all:
		if s.type == 'COLOR' and s.name != 'mask':
			strips.append(s)
	strips = sorted(strips, key=lambda s: s.frame_final_start, reverse = False)
	for i, s in enumerate(strips):	
			try: 
				s.name = List[i]
			except: s.name = ''



def update_caption_list():
	global List
	try: the_file = str(bpy.types.Scene.sub_file)
	except: the_file = ''
	text = bpy.data.texts[the_file].as_string()
	List = text.splitlines()

def exists(obj):
	file_exists = False
	for ob in bpy.context.screen.scene.objects:
		if ob.name == obj:
			file_exists = True
			break

def timecode(frame):
	tc = '{0:02d}:{1:02d}:{2:02d}:{3:02d}'.format(int(frame / (3600*framerate)),
													int(frame / (60*framerate) % 60),
													int(frame / framerate % 60),
													int(frame % framerate))
	return tc

def setup():
	original_type = bpy.context.area.type
	bpy.context.area.type = "SEQUENCE_EDITOR"	 
	for s in bpy.context.scene.sequence_editor.sequences:
		if s.type == 'MOVIE':
			y = s.elements[0].orig_height
			x = s.elements[0].orig_width
			rnd = bpy.data.scenes[0].render
			rnd.resolution_x = x
			rnd.resolution_y = y
			bpy.ops.screen.frame_jump(end=False)
			bpy.context.screen.scene.frame_end = s.frame_final_end

		if s.type == 'SOUND':
			bpy.context.scene.sequence_editor.active_strip = s
			s.show_waveform = True
			bpy.ops.sequencer.view_selected()
	bpy.context.area.type = original_type

def find_sub():
	global strips
	frame = bpy.context.scene.frame_current
	for i, t in enumerate(strips):
		if frame > t.frame_final_start and frame < t.frame_final_end:
			new = t.name
			try: next = strips[i+1].name
			except:	next = ''
			return new, next
	return '',''
	
def update_sub():
	strip_list()
	current = bpy.data.objects['current'].data.body
	new, next = find_sub()
	if current != new :
		bpy.data.objects['current'].data.body = new
		bpy.data.objects['next'].data.body = next
	frame = bpy.context.scene.frame_current
	bpy.data.objects['tc'].data.body = timecode(frame)
		#bpy.ops.sequencer.refresh_all()

def new_sub_strip(start):
	global current_strip, adding_sub
	seq = bpy.ops.sequencer
	seq.effect_strip_add(frame_start=start, frame_end=start+1, type='COLOR', color=(random.uniform(0.5,1),random.uniform(0.5,1),1), overlap=False)
	current_strip = bpy.context.scene.sequence_editor.active_strip
	current_strip.blend_alpha = 0
	adding_sub = True
	return

def end_strip(frame):
	global current_strip, adding_sub
	current_strip.frame_final_end = frame - 1
	adding_sub = False
	current_strip = None

# Everything that needs to be done when the frame changes
def main(self):
	global adding_sub, current_strip
	update_sub()
	if adding_sub:
		current_strip.frame_final_end = bpy.context.scene.frame_current + 1

''' ------------------------------------------------------------------------------'''
'''                                 INTERFACE                                     '''
''' ------------------------------------------------------------------------------'''

class OBJECT_OT_Setup(bpy.types.Operator):  
	bl_label = "Setup"
	bl_idname = "sequencer.setup"
	bl_description = "Setup the scene (needs a video sequence already in place)"
		
	def invoke(self, context, event):
		setup()
		return {'FINISHED'}

class OBJECT_OT_Refresh(bpy.types.Operator):  
	bl_label = "Refresh"
	bl_idname = "sequencer.refresh"
	bl_description = "Re-adapt the captions configuration to you sequence"
		
	def invoke(self, context, event):
		refresh()
		return {'FINISHED'}	
	
class OBJECT_OT_Export(bpy.types.Operator):
	bl_label = "Export Subtitles"
	bl_idname = "sequencer.export"
	bl_description = "Export Fab-ish formated file"
		
	def invoke(self, context, event):
		sub_to_file()
		return {'FINISHED'}

class OBJECT_OT_Insert_start(bpy.types.Operator):  
	bl_label = ""
	bl_idname = "sequencer.sub_start"
	bl_description = "start"
		
	def invoke(self, context, event):
		global adding_sub, current_strip
		original_type = bpy.context.area.type
		bpy.context.area.type = "SEQUENCE_EDITOR"
		frame = bpy.context.scene.frame_current
		if adding_sub:
			end_strip(frame)
		new_sub_strip(frame)
		strip_list()
		'''if bpy.context.screen.scene.snap == True:
			bpy.ops.marker.move(frames=-(frame - snap_to(frame,'start')))'''
		bpy.context.area.type = original_type
		return {'FINISHED'}
		
class OBJECT_OT_Insert_end(bpy.types.Operator):  
	bl_label = ""
	bl_idname = "sequencer.sub_end"
	bl_description = "end"
		
	def invoke(self, context, event):
		global adding_sub, current_strip
		original_type = bpy.context.area.type
		bpy.context.area.type = "SEQUENCE_EDITOR"
		frame = bpy.context.scene.frame_current
		if adding_sub:
			end_strip(frame)
		
		'''if bpy.context.screen.scene.snap == True:
			frame = bpy.context.scene.frame_current
			bpy.ops.marker.move(frames=-(frame - snap_to(frame,'end')))'''
		bpy.context.area.type = original_type
		return {'FINISHED'}

class Sub_Chooser(bpy.types.Operator):
	bl_idname = "object.menu"
	bl_label = "All the texts from the Text Editor"

	text_name = bpy.props.StringProperty(name="caption_file_name")
	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):	
		bpy.types.Scene.sub_file = self.text_name
		update_caption_list()
		return {'FINISHED'}

class Sub_Chooser_Menu(bpy.types.Menu):
	bl_label = "Where are your subtitles?"
	bl_idname = "OBJECT_MT_sub_chooser"

	def draw(self, context):
		layout = self.layout
		for txt in bpy.data.texts:
			props = layout.operator("object.menu", text=txt.name)
			props.text_name = txt.name
			
def draw_item(self, context):
	layout = self.layout
	layout.menu(Sub_Chooser_Menu.bl_idname)

class Caption_Menu(bpy.types.Menu):
	bl_label = "Subtitles Menu"
	bl_idname = "OBJECT_MT_caption_menu"

	def draw(self, context):
		layout = self.layout
		layout.menu(Sub_Chooser_Menu.bl_idname)
		layout.operator("sequencer.setup")
		layout.operator("sequencer.refresh")
		layout.operator("sequencer.export")

def draw_item(self, context):
	layout = self.layout
	layout.menu(Caption_Menu.bl_idname)
			   
class iop_panel(bpy.types.Header):	 
	bl_space_type = "SEQUENCE_EDITOR"	   
	bl_region_type = "UI"		  
	bl_label = "subtitles"
	global main_scene
	
	@classmethod
	def poll(self, context):
		return True
	
	def draw(self, context):
		layout = self.layout
		layout.separator()
		row=layout.row()
		row.operator("sequencer.sub_start", icon="TRIA_RIGHT")
		row.operator("sequencer.sub_end", icon="TRIA_LEFT")
		row.prop(context.scene,"snap")

def register():
	bpy.app.handlers.frame_change_post.append(main)
	bpy.utils.register_class(iop_panel)
	bpy.utils.register_class(OBJECT_OT_Insert_start)
	bpy.utils.register_class(OBJECT_OT_Insert_end)
	bpy.utils.register_class(OBJECT_OT_Export)
	bpy.utils.register_class(OBJECT_OT_Setup)
	bpy.utils.register_class(OBJECT_OT_Refresh)
	bpy.utils.register_class(Sub_Chooser_Menu)
	bpy.utils.register_class(Sub_Chooser)
	bpy.utils.register_class(Caption_Menu)
	bpy.types.INFO_HT_header.append(draw_item)
	
def unregister():
	bpy.app.handlers.frame_change_post.remove(main)
	bpy.utils.unregister_class(iop_panel)
	bpy.utils.unregister_class(OBJECT_OT_Insert_start)
	bpy.utils.unregister_class(OBJECT_OT_Insert_end)
	bpy.utils.unregister_class(OBJECT_OT_Export)
	bpy.utils.unregister_class(OBJECT_OT_Setup)
	bpy.utils.unregister_class(OBJECT_OT_Refresh)
	bpy.utils.unregister_class(Sub_Chooser_Menu)
	bpy.utils.unregister_class(Sub_Chooser)
	bpy.utils.unregister_class(Caption_Menu)
	bpy.types.INFO_HT_header.remove(draw_item)

if __name__ == "__main__":
	register()
	
