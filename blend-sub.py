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
''' version 0.1b '''
''' ------------------------------------------------------------------------------'''
'''					  IMPORT / PROPERTIES / VARIABLES						  '''
''' ------------------------------------------------------------------------------'''
import bpy, random
from bpy.app.handlers import persistent

bpy.types.Scene.snap = bpy.props.BoolProperty(name="Snap",description="Snap subtitles to the highest sound level around",default = False)
bpy.types.Scene.lock = bpy.props.BoolProperty(name="Lock",description="Lock for rendering subtitles",default = False)
bpy.types.Scene.sub_file = bpy.props.StringProperty(name="Caption_file_name")
bpy.types.Scene.sub_file = ''
global strips, adding_sub, current_strip, framerate, current_scene

adding_sub = False
current_scene = '' # will be initialized later for safety

''' ------------------------------------------------------------------------------'''
'''								 FUNCTIONS									 '''
''' ------------------------------------------------------------------------------'''

# Bake the vu-meter
def refresh():
	path = ''
	original_type = bpy.context.area.type
	bpy.context.area.type = "SEQUENCE_EDITOR"
	for s in bpy.context.scene.sequence_editor.sequences:
		if s.type == 'SOUND':
			path = bpy.path.abspath(s.filepath) 
			pass
	if exists('vu') and path != '' :
		bpy.context.area.type = "VIEW_3D";
		bpy.ops.object.select_all(action='DESELECT')	 
		vu = bpy.data.objects['vu']
		bpy.ops.object.select_pattern(pattern="vu")
		bpy.ops.anim.keyframe_insert_menu(type = "Scaling")
		vu.animation_data.action.fcurves[0].lock = True
		vu.animation_data.action.fcurves[2].lock = True
		bpy.context.area.type = "GRAPH_EDITOR";
		try: bpy.ops.graph.sound_bake(filepath=path, low=(40), high=(1500))
		except: print('Sorry, failed to analyse the sound sequence.')
		bpy.context.area.type = "VIEW_3D";
		bpy.context.scene.objects.active = vu
		bpy.ops.object.select_pattern(pattern="vu")  
		vu.animation_data.action.fcurves[0].lock = False
		vu.animation_data.action.fcurves[2].lock = False 
	bpy.context.area.type  = original_type 

# snap to sound peak around
def snap_to(frame, type):
	vu = bpy.data.objects['vu']
	temp = []
	framerate = bpy.context.scene.render.fps
	range_from = frame - framerate
	for f in range(range_from,frame):
		try : temp.append([vu.animation_data.action.fcurves[1].evaluate(f),f])
		except : pass
	if type == 'start' : temp.sort(reverse=True)
	else : temp.sort()
	if len(temp) > 0 : return temp[0][1]
	else : return frame

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
	if len(str(bpy.types.Scene.sub_file)) > 1 :
		try: the_file = str(bpy.types.Scene.sub_file)
		except: the_file = ''
		text = bpy.data.texts[the_file].as_string()
		List = text.splitlines()
	else : List = []

def exists(obj):
	global current_scene
	if obj in current_scene.objects : return True
	else : return False

def timecode(frame):
	framerate = bpy.context.scene.render.fps
	tc = '{0:02d}:{1:02d}:{2:02d},{3:02d}'.format(int(frame / (3600*framerate)),
													int(frame / (60*framerate) % 60),
													int(frame / framerate % 60),
													int(frame % framerate))
	return tc

def setup():
	global current_scene
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
			current_scene.frame_end = s.frame_final_end

		if s.type == 'SOUND':
			bpy.context.scene.sequence_editor.active_strip = s
			s.show_waveform = True
			bpy.ops.sequencer.view_selected()
	
	scene = bpy.context.scene.name
	bpy.ops.sequencer.select_all(action = "DESELECT")
	for s in bpy.context.scene.sequence_editor.sequences:
		if s.name == 'mask' :
			s.select = True
		if s.type == 'SCENE' and s.name == scene :
			s.select = True
	bpy.ops.sequencer.delete()

	if 'mask' not in bpy.context.scene.sequence_editor.sequences :
		bpy.ops.sequencer.select_all(action = "DESELECT")
		end = bpy.context.scene.frame_end
		res_y = bpy.data.scenes[0].render.resolution_y
		offset = res_y - (res_y//7)
		bpy.ops.sequencer.effect_strip_add(frame_start=1, frame_end=end, channel=3, type='COLOR')
		mask = bpy.context.scene.sequence_editor.active_strip
		mask.name = 'mask'
		mask.use_translation = True
		mask.transform.offset_y = -offset
		mask.blend_alpha = 0.4
		mask.blend_type = 'ALPHA_OVER'

	if scene not in bpy.context.scene.sequence_editor.sequences :
		bpy.ops.sequencer.select_all(action = "DESELECT")
		bpy.ops.sequencer.scene_strip_add(frame_start=1, channel=4, scene=scene)
		s = bpy.context.scene.sequence_editor.active_strip
		s.blend_type = 'ALPHA_OVER'
		
	refresh()
	bpy.context.area.type = original_type


def find_sub(frame):
	global strips, List
	for i, t in enumerate(strips):
		if frame > t.frame_final_start and frame < t.frame_final_end:
			new = t.name
			next = List[i+1]
			return new, next
	return '',''
	
def update_sub(frame):
	global current_scene
	if current_scene.lock == False:
		strip_list()
	current = bpy.data.objects['current'].data.body
	new, next = find_sub(frame)
	if current != new :
		if exists('current') : bpy.data.objects['current'].data.body = clean(new,'/')
		if exists('next') and current_scene.lock == False : bpy.data.objects['next'].data.body = clean(next,'/')
	if exists('tc') and current_scene.lock == False :
		bpy.data.objects['tc'].data.body = timecode(frame)

def new_sub_strip(start):
	global current_strip, adding_sub, current_scene
	seq = bpy.ops.sequencer
	seq.effect_strip_add(frame_start=start, frame_end=start+1, type='COLOR', color=(random.uniform(0.5,1),random.uniform(0.5,1),1), overlap=False)
	current_strip = bpy.context.scene.sequence_editor.active_strip
	current_strip.blend_alpha = 0
	if current_scene.snap == True:
		current_strip.frame_final_start = snap_to(start,'start')
	return True

def end_strip(frame):
	global current_strip, adding_sub, current_scene
	current_strip.frame_final_end = frame - 1
	if current_scene.snap == True:
			current_strip.frame_final_end = snap_to(frame,'start')
	current_strip = None
	return True

def clean(str,x):
	return str.replace(x, '\n')

def sub_to_file():
		sub_text = bpy.data.texts.new(bpy.types.Scene.sub_file + '.srt')
		for i,l in enumerate(strips):
			sub_text.write(str(i+1) + '\n' + timecode(l.frame_final_start) + ' --> ' + timecode(l.frame_final_end) + '\n' + l.name + '\n\n')


# Everything that needs to be done when the frame changes
def main(self):
	global adding_sub, current_strip
	frame = bpy.context.scene.frame_current
	if adding_sub:
		current_strip.frame_final_end = bpy.context.scene.frame_current + 10
	update_sub(frame)
	

''' ------------------------------------------------------------------------------'''
'''								 INTERFACE									 '''
''' ------------------------------------------------------------------------------'''

class OBJECT_OT_Setup(bpy.types.Operator):  
	bl_label = "Setup"
	bl_idname = "sequencer.setup"
	bl_description = "Setup the scene (needs a video sequence already in place)"
		
	def invoke(self, context, event):
		setup()
		return {'FINISHED'}

class OBJECT_OT_Refresh(bpy.types.Operator):  
	bl_label = "Analyse the sound"
	bl_idname = "sequencer.refresh"
	bl_description = "Initialize the vu-meter for snapping feature"
		
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
	bl_label = "Add"
	bl_idname = "sequencer.sub_start"
	bl_description = "start"

	def invoke(self, context, event):
		global adding_sub, current_strip
		if len(str(bpy.types.Scene.sub_file)) > 1 :
			original_type = bpy.context.area.type
			bpy.context.area.type = "SEQUENCE_EDITOR"
			frame = bpy.context.scene.frame_current
			if adding_sub:
				end_strip(frame)
			adding_sub = new_sub_strip(frame)
			strip_list()
			bpy.context.area.type = original_type
		return {'FINISHED'}
		
class OBJECT_OT_Insert_end(bpy.types.Operator):  
	bl_label = "End"
	bl_idname = "sequencer.sub_end"
	bl_description = "end"
		
	def invoke(self, context, event):
		global adding_sub, current_strip
		if len(str(bpy.types.Scene.sub_file)) > 1 :
			original_type = bpy.context.area.type
			bpy.context.area.type = "SEQUENCE_EDITOR"
			frame = bpy.context.scene.frame_current
			if adding_sub:
				if end_strip(frame) : adding_sub = False
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
		# initialize the current_scene here
		global current_scene
		current_scene = bpy.context.screen.scene
		#
		layout = self.layout
		for txt in bpy.data.texts:
			if '.fab' not in txt.name and '.py' not in txt.name :
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
		row.prop(context.scene,"lock")

def register():
	bpy.app.handlers.frame_change_pre.append(main)
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
	bpy.app.handlers.frame_change_pre.remove(main)
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
	
