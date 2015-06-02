import bpy, pickle, os

save_file = os.path.expanduser('~/%s.ez' % 'save')
open(save_file, 'a').close()
s = bpy.context.scene
pickle.dump(s, open( save_file, "wb" ) )