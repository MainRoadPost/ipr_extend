"""
The parameters to the script are contained in the kwargs dictionary:
    kwargs["viewer"]    The hou.IPRViewer pane tab
    kwargs["position"]  A tuple of two ints containing the pixel position
    kwargs["slot"]      An integer indicating which script slot was chosen
"""
from __future__ import print_function
import __future__
import hdefereval
depth = None
prim=None
viewer = kwargs["viewer"]
px, py = kwargs["position"]
slot = kwargs["slot"]
material = viewer.materialNode(px, py)
style_sheet_paths = viewer.evaluatedStyleSheetPaths(px, py)
if "Pz" in viewer.planes():
 depth=viewer.pixel("Pz", px, py)[0]
mantra=viewer.ropNode()

if mantra is not None:
 camera=hou.node(hou.parm(mantra.path()+'/camera').eval())
 if camera is not None:
    focus=hou.parm(camera.path()+'/focus')

pmats=[]
    
def select_tree(tree, paths):
    tree.clearCurrentPath()
    for path in paths:
        tree.setCurrentPath(path[0], True, path[1]+3)

def get_pane(pane_type):
    index = 0
    pane = None

    while True:
        pane = hou.ui.paneTabOfType(pane_type, index)

        if pane is None:
            break

        if pane.isFloating():
            break

        index += 1

    return pane

if slot is 0:
    window = None
    parm_pane = None
    if material is not None:
        # Display a floating parameter window for the material.
        parm_pane = get_pane(hou.paneTabType.Parm)
        if not parm_pane:
            window = hou.ui.curDesktop().createFloatingPanel(hou.paneTabType.Parm)
            parm_pane = window.paneTabs()[0]

        parm_pane.setCurrentNode(material)
        parm_pane.setPin(True)
        parm_pane.setIsCurrentTab()

    if len(style_sheet_paths) > 0:
        # Select style sheets in the data tree
        tree_pane = get_pane(hou.paneTabType.DataTree)
        if not tree_pane:
            if window:
                pane1 = window.panes()[0]
                tree_pane = pane1.createTab(hou.paneTabType.DataTree)
            else:
                if parm_pane:
                    tree_pane = parm_pane.pane().createTab(hou.paneTabType.DataTree)
                else:
                    window = hou.ui.curDesktop().createFloatingPanel(hou.paneTabType.DataTree)
                    tree_pane = window.paneTabs()[0]

        tree_pane.setTreeType("Material Style Sheets")
        tree_pane.setIsCurrentTab()

        # Todo: Figure out a better way to handle this, perhaps by hooking into
        # some sort of panel event. Something in the data tree intialization order
        # causes a direct call to setCurrentPaths to have no effect if a new data
        # tree is created. We need to wait a bit until the data tree is initialized,
        # and then set the paths.
        hdefereval.executeDeferredAfterWaiting(
                        lambda: select_tree(tree_pane, style_sheet_paths),
                                num_waits=2)

else:
    # Display information about the pixel in a popup window.
    rop_node_name = viewer.ropNode()

    obj_node = viewer.objectNode(px, py)
    if obj_node is not None:
        heading = "Pixel Information"
    else:
        heading = "No shader detected under the cursor"
    if viewer.ropNode() is not None:
      message = (
        "IPR Viewer: %s\n" % viewer.ropNode().path() +
        "Pixel: %d %d\n" % (px, py))
    else:
     message = ("")

    if obj_node is not None:
        prim = viewer.prim(px, py)
        packedmess=''
        try:
            if prim.type().name()=='PackedPrim':
                basemat=""
                try:
                    basemat=prim.attribValue('shop_materialpath')
                except:
                    pass
                
                packedmess='PackedPath:'+prim.intrinsicValue('filename')+"\n"
                if basemat=="":
                    tmpnode=hou.node('/obj/ipr_helper1')
                    if tmpnode is None:
                        tmpnode=hou.node('/obj').createNode('ipr_helper')
                    try:    
                        tmpnode.parm('packed').set(prim.intrinsicValue('filename'))
                        geo=hou.node(tmpnode.path()+'/load_tmp').geometry()
                        packedmats=geo.primStringAttribValues('shop_materialpath')
                        pmats=set(list(packedmats))
                        packedmess+='PackedMaterials:'+"\n"
                        for p in pmats:
                            packedmess+=p+"\n"
                        tmpnode.destroy()
                    except:
                        pass
                    try:
                        if tmpnode is not None:
                            tmpnode.destroy()
                    except:
                        pass
                else:
                    packedmess+='PackedMaterial:'+basemat+"\n"
                    
            elif prim.type().name()=='Agent':
                basemat=""
                try:
                    basemat=prim.attribValue('shop_materialpath')
                except:
                    pass
                
                agent=prim.definition()
                shapes=agent.shapeLibrary()
                filename=shapes.fileName()
                packedmess='PackedPath:'+filename+"\n"
                if basemat=="":
                    tmpnode=hou.node('/obj/ipr_helper1')
                    if tmpnode is None:
                        tmpnode=hou.node('/obj').createNode('ipr_helper')
                    try:    
                        tmpnode.parm('packed').set(filename)
                        geo=hou.node(tmpnode.path()+'/extract').geometry()
                        packedmats=geo.primStringAttribValues('shop_materialpath')
                        pmats=set(list(packedmats))
                        packedmess+='PackedMaterials:'+"\n"
                        for p in pmats:
                            packedmess+=p+"\n"
                        tmpnode.destroy()
                    except:
                        pass
                    try:
                        if tmpnode is not None:
                            tmpnode.destroy()
                    except:
                        pass
                else:
                    packedmess+='PackedMaterial:'+basemat+"\n"
                
        except:
            pass
        prim_info = (" (primitive %d)" % prim.number() if prim is not None
            else "")
        message += (
            "Object: %s\n" % obj_node.path() +
            "Geometry: %s%s\n" % (obj_node.renderNode().path(), prim_info))
        if packedmess!='':
            message +=packedmess

    material = viewer.materialNode(px, py)
    if material is not None:
        message += "Material: %s\n" % material.path()

    for plane in viewer.planes():
        value = viewer.pixel(plane, px, py)
        if len(value) == 1:
            value = value[0]
        message += "    Plane %s: %s\n" % (plane, value)

def excludeObj():
    excludeparm=mantra.parm('excludeobject')
    if excludeparm is not None and obj_node is not None and obj_node.renderNode() is not None:
        nodepath=obj_node.renderNode().path()
        exclude=excludeparm.eval().split(' ')
        objnpath=obj_node.path()
        objnname=obj_node.name()
        if objnpath not in exclude and objnname not in exclude:
            exclude.append(objnpath)

        new_exclude=' '.join(exclude)
        excludeparm.set(new_exclude)
        
def matteObj():
    matteparm=mantra.parm('matte_objects')
    if matteparm is not None and obj_node is not None and obj_node.renderNode() is not None :
        nodepath=obj_node.renderNode().path()
        matte=matteparm.eval().split(' ')
        objnpath=obj_node.path()
        objnname=obj_node.name()
        if objnpath not in matte and objnname not in matte:
            matte.append(objnpath)
        else:
            matte.remove(objnpath)

            
        new_exclude=' '.join(matte)
        matteparm.set(new_exclude)
        
#####Light Selection Functions
def getallLights():
    key = ('light','sun')
    all_instances = []
    for node_type in hou.objNodeTypeCategory().nodeTypes().values():
        components = node_type.nameComponents()
        for k in key:
            if k in components[2]:
                all_instances.extend(node_type.instances())
    return all_instances

def selectlight():
    try:
        lightarr=[]
        light_path=viewer.displayedPlane()
        lnm=light_path.split('_all')
        if len(lnm)==2 and lnm[1]!='':
            num=int(lnm[1].replace('_',''))
            for l in getallLights():
                if l.name()==lnm[0]:
                    lightarr.append(l)
            curlight=lightarr[num+1]
        else:
            for l in getallLights():
                if l.name()==lnm[0]:
                    curlight=l
                    break 
        if curlight.isInsideLockedHDA():
            path=(curlight.path()).split('/')
            for p in range(len(path)):
                path.pop()
                curlight=hou.node('/'.join(path))
                if curlight.isInsideLockedHDA()==False:
                    break

        curlight.setCurrent(1,True)
    except:
        pass

###### Light Selection Functions End   
    
def phantomObj():
    phantomparm=mantra.parm('phantom_objects')
    if phantomparm is not None and obj_node is not None and obj_node.renderNode() is not None:
        nodepath=obj_node.renderNode().path()
        phantom=phantomparm.eval().split(' ')
        objnpath=obj_node.path()
        objnname=obj_node.name()
        if objnpath not in phantom and objnname not in phantom:
            phantom.append(objnpath)
        else:
            phantom.remove(objnpath)

        new_exclude=' '.join(phantom)
        phantomparm.set(new_exclude)                
        
def isolateobj():
    json=hou.getenv('HIP')+'/'+hou.getenv('HIPNAME')+'_'+mantra.name()+'json'
    parms=['vobject','forceobject','matte_objects','phantom_objects','exclude_object']
    


    
style_sheet = viewer.evaluatedStyleSheetJSON(px, py)
#####Buttons Setup
buttons=list(['OK'])
#if viewer.displayedPlane()=='C':
buttons+=list(['Select Shader','Select Node','Matte','Phantom','Exclude'])
if depth != None and mantra is not None and camera is not None:
    buttons+=list(['Fiocal Point'])
    #if prim != None and prim.type().name()=='PackedPrim':   
    #    buttons+=list(['Isolate'])
if '_all' in (viewer.displayedPlane()):
    buttons+=list(['Select Current Light'])

####Buttons Setup End

answer=hou.ui.displayMessage(heading, buttons , severity=hou.severityType.Message, default_choice=0, close_choice=0,help=message, details=style_sheet, details_label="Show Evaluated Material Style Sheet")
button=buttons[answer]

ispacked=0
try:
    tp=prim.type().name()
    if tp=='PackedPrim' or tp=='Agent':
        ispacked=1
except:
    pass

if button is 'Select Shader':
    if material is not None:
        material.setSelected(1,1)
    elif ispacked==1 and len(pmats)>0:
        try:
            choose=hou.ui.selectFromList(tuple(pmats), exclusive=True,title='Choose Shader from Packed')
            val=str(tuple(pmats)[choose[0]])
            material=hou.node(val)
            if material is not None:
                material.setSelected(1,1)
            else:
                print('Material not Found!!!')
        except:
            pass
        
elif button is'Select Node':
    if obj_node is not None:
        nodepath=obj_node.path()
        if nodepath is not None:
            hou.node(nodepath).setSelected(1,1)
        else:
            obj_node.setSelected(1,1)
elif button is 'Fiocal Point' and focus !=None and (depth>0):
	focus.set(depth)
		
elif button is 'Matte':
    matteObj()                
elif button is 'Phantom':
    phantomObj()                
elif button is 'Exclude':
    excludeObj()
elif button is 'Select Current Light':
    selectlight()
elif button is 'Isolate':
    isolateobj()	

