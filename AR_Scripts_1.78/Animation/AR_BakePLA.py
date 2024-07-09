"""
AR_BakePLA

Author: Arttu Rautio (aturtur)
Website: http://aturtur.com/
Name-US: AR_BakePLA
Version: 1.1.2
Description-US: Bakes quickly object to Point Level Animation (PLA)

To bake splines, bake them first to alembic and then use this script to bake the alembic file to PLA.
It's important that 'Intermediate Points' is set to 'Uniform'!

Written for Maxon Cinema 4D 2023.1.0
Python version 3.9.1

Change log:
1.1.2 (26.04.2024) - Disables Alembic Morph tag on baked object
1.1.1 (24.09.2023) - Status bar fix, returns to frame where you started baking
1.1.0 (18.11.2022) - Parallel processing, bakes multiple cameras in one go. Progress bar
1.0.3 (05.03.2022) - Removed User Data Xpresso Object Node hack
1.0.2 (10.10.2021) - Updated to R25
1.0.1 (27.10.2020) - Fixed setTime bug

To do:
- Better handling with splines
"""

# Libraries
import c4d
from c4d import utils as u

# Global variables
suffix = "_baked"

# Functions
def MakeEditable(op):
    if (op != None) and op.GetType() not in [5100, 5101]:
        clone = op.GetClone() # Get clone
        clone.SetMg(op.GetMg()) # Set global matrix
        doc.InsertObject(clone) # Insert clone to document
        bc = c4d.BaseContainer() # Initialize Base Container
        makeEditable = c4d.MCOMMAND_MAKEEDITABLE # Mcommand 'Make Editable'
        op = c4d.utils.SendModelingCommand(makeEditable, [clone], 0, bc, doc) # Make editable
        if op: return op[0] # Return object
    else:
        return op.GetClone()

def DisableTags(objects):
    for obj in objects: # Iterate through objects
        theObj = obj[2] # Baked object
        tags = theObj.GetTags() # Get objects tags
        for t in tags: # Iterate through tags
            if t.GetType() == 180000102: # If dynamics tag (bullet)
                t[c4d.RIGID_BODY_ENABLED] = False # Disable dynamics
            if t.GetType() == 100004020: # If cloth tag
                t[c4d.CLOTH_USE] = False # Disable cloth
            if t.GetType() == 1018068: # If spline dynamics tag
                t[c4d.EXPRESSION_ENABLE] = False # Disable spline dynamics
            if t.GetType() == 1059981: # If rigid body tag (new simulation system)
                t[c4d.RIGIDBODY_USE] = False # Disable dynamics
            if t.GetType() == 1037184: # If alembic morph tag
                t[c4d.EXPRESSION_ENABLE] = False # Disable alembic tag

def DummyObject(obj, doc):
    dummyObject = MakeEditable(obj) # Get clone from original object

    """
    if dummyObject.GetType() == 5101: # If spline object
        rpc = len(dummyObject.GetAllPoints())
        dummyObject.ResizeObject(rpc, -1) # Set new point count
    """

    RemoveTags(dummyObject) # Remove tags of the object

    # Clean
    if dummyObject.GetCTracks() != None:
        for cTrack in dummyObject.GetCTracks(): cTrack.Remove() # Remove unnecessary tracks
    ResetPSR(dummyObject) # Reset PSR
    children = dummyObject.GetChildren() # Remove children
    for c in children:
        c.Remove()

    dummyObject.SetName("Dummy "+obj.GetName()) # Set name
    doc.InsertObject(dummyObject) # Insert dummyObject to document
    MoveToLast(dummyObject, doc) # Move new Object in the object hierarchy

    xpressoTag = c4d.BaseTag(c4d.Texpresso) # Initialize a xpresso tag
    dummyObject.InsertTag(xpressoTag)
    prioritydata = c4d.PriorityData() # Initialize a priority data
    prioritydata.SetPriorityValue(c4d.PRIORITYVALUE_MODE, c4d.CYCLE_GENERATORS) # Set priority to 'Generators'
    prioritydata.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 449) # Set priority value to last possible value
    prioritydata.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, False) # Set Object dependent to false
    xpressoTag[c4d.EXPRESSION_PRIORITY] = prioritydata # Set priority data

    #link1 = CreateUserDataLink(dummyObject, "Source", obj) # Create user data link
    #link2 = CreateUserDataLink(dummyObject, "Dummy", dummyObject) # Create user data link

    nodemaster = xpressoTag.GetNodeMaster() # Get node master

    # Create nodes
    objectNodeA = nodemaster.CreateNode(nodemaster.GetRoot(), 400001000, None, x=0, y=100) # Create object node
    objectNodeB = nodemaster.CreateNode(nodemaster.GetRoot(), 400001000, None, x=300, y=0) # Create 2nd object node
    pythonNode = nodemaster.CreateNode(nodemaster.GetRoot(), 1022471, None, x=100, y=250) # Create python node
    pointNodeA = nodemaster.CreateNode(nodemaster.GetRoot(), 400001112, None, x=300, y=150) # Create point node
    pointNodeB = nodemaster.CreateNode(nodemaster.GetRoot(), 400001112, None, x=600, y=150) # Create 2nd point node
    iterationNode = nodemaster.CreateNode(nodemaster.GetRoot(), 400001131, None, x=350, y=300) # Create iteration node

    # Modify python node
    pythonNode.RemoveUnusedPorts() # Remove default ports
    pyInPort   = pythonNode.AddPort(c4d.GV_PORT_INPUT, 4013, c4d.GV_PORT_FLAG_IS_VISIBLE) # Add input link port
    pyInPort.SetName("Input1") # Set port's name
    pyOutPortA = pythonNode.AddPort(c4d.GV_PORT_OUTPUT, 4012, c4d.GV_PORT_FLAG_IS_VISIBLE) # Add output link port
    pyOutPortA.SetName("Output1") # Set port's name
    pyOutPortB = pythonNode.AddPort(c4d.GV_PORT_OUTPUT, 4000, c4d.GV_PORT_FLAG_IS_VISIBLE) # Add output integer port
    pyOutPortB.SetName("Output2") # Set port's name
    pythonNode[c4d.GV_PYTHON_CODE] = ("import c4d\n"
                                     "def main():\n"
                                     "\tglobal Output1\n"
                                     "\tglobal Output2\n"
                                     "\tif Input1.GetType() not in [5100, 5101]:\n"
                                     "\t\tcache = Input1.GetCache()\n"
                                     "\t\tpntCnt = len(cache.GetAllPoints())\n"
                                     "\telif Input1.GetType() == 5100:\n" # Polygon object
                                     "\t\tcache = Input1\n"
                                     "\t\tpntCnt = len(cache.GetAllPoints())\n"
                                     "\telif Input1.GetType() == 5101:\n" # Spline object
                                     "\t\tcache = Input1.GetRealSpline()\n"
                                     "\t\tpntCnt = len(cache.GetAllPoints())\n"
                                     "\tOutput1 = cache\n"
                                     "\tOutput2 = int(pntCnt)-1") # Python node's code

    # Modify object node A
    objectNodeA[c4d.GV_OBJECT_OBJECT_ID] = obj
    objPortA = objectNodeA.AddPort(c4d.GV_PORT_OUTPUT, 40000002, c4d.GV_PORT_FLAG_IS_VISIBLE)
    #objectNodeA[c4d.GV_OBJECT_OBJECT_ID] = dummyObject
    #objPortA = objectNodeA.AddPort(c4d.GV_PORT_OUTPUT, # Add 'user data link' output port to node
        #c4d.DescID(c4d.DescLevel(c4d.ID_USERDATA, c4d.DTYPE_SUBCONTAINER, 0),c4d.DescLevel(1)), message=True)


    # Modify object node B
    objectNodeB[c4d.GV_OBJECT_OBJECT_ID] = dummyObject
    objPortB = objectNodeB.AddPort(c4d.GV_PORT_OUTPUT, 40000002, c4d.GV_PORT_FLAG_IS_VISIBLE)
    #objectNodeB[c4d.GV_OBJECT_OBJECT_ID] = dummyObject
    #objPortB = objectNodeB.AddPort(c4d.GV_PORT_OUTPUT, # Add 'user data link' output port to node
        #c4d.DescID(c4d.DescLevel(c4d.ID_USERDATA, c4d.DTYPE_SUBCONTAINER, 0),c4d.DescLevel(2)), message=True)

    # Modify point nodes
    pointNodeA[c4d.GV_POINT_USE_DEFORMED] = True
    pointNodeB[c4d.GV_POINT_USE_DEFORMED] = True
    pointNodeB.AddPort(c4d.GV_PORT_INPUT, 2002, c4d.GV_PORT_FLAG_IS_VISIBLE) # Add input point position port

    # Connecting ports
    objPortA.Connect(pyInPort)
    objPortB.Connect(pointNodeB.GetInPort(0))

    pyOutPortA.Connect(pointNodeA.GetInPort(0))
    pyOutPortB.Connect(iterationNode.GetInPort(1))
    iterationNode.GetOutPort(0).Connect(pointNodeA.GetInPort(1))
    iterationNode.GetOutPort(0).Connect(pointNodeB.GetInPort(1))
    pointNodeA.GetOutPort(1).Connect(pointNodeB.GetInPort(2))

    c4d.modules.graphview.RedrawMaster(nodemaster) # Refresh xpresso
    return dummyObject

def MoveToLast(obj, doc):
    items = doc.GetObjects() # Get top level items from the document
    last = items[-1] # The Last item in the hierarchy
    obj.InsertAfter(last) # Move object after the last item

def MoveToFirst(obj, doc):
    items = doc.GetObjects() # Get top level items from the document
    first = items[0] # The first item in the hierarchy
    obj.InsertBefore(first) # Move object before the first item

def CopyTags(objects):
    for obj in objects: # Iterate through objects
        source = obj[0] # Source object
        target = obj[2] # Bake object
        hiddenTags = [c4d.PointTag, c4d.PolygonTag] # Tag types that you dont wan't to delete
        tags = source.GetTags() # Get objects tags
        for t in reversed(tags): # Iterate through tags
            if type(t) not in hiddenTags:
                d = t.GetClone() # Duplicate the tag
                target.InsertTag(d) # Copy tag

def RemoveDummys(objects):
    for obj in objects: # Iterate through objects
        dummy = obj[1] # Dummy object
        dummy.Remove() # Delete dummy object

def ResetPSR(op):
    op[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_X] = 0
    op[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Y] = 0
    op[c4d.ID_BASEOBJECT_REL_POSITION,c4d.VECTOR_Z] = 0
    op[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_X] = 1
    op[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Y] = 1
    op[c4d.ID_BASEOBJECT_REL_SCALE,c4d.VECTOR_Z] = 1
    op[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_X] = 0
    op[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Y] = 0
    op[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = 0

def CreateUserDataLink(obj, name, link, parentGroup=None, shortname=None):
    """ Create user data link """
    if obj is None: return False # If there is no object stop the function
    if shortname is None: shortname = name # Short name is name
    bc = c4d.GetCustomDatatypeDefault(c4d.DTYPE_BASELISTLINK) # Initialize user data
    bc[c4d.DESC_NAME] = name # Set user data name
    bc[c4d.DESC_SHORT_NAME] = shortname # Set userdata short name
    bc[c4d.DESC_DEFAULT] = link # Set default value
    bc[c4d.DESC_ANIMATE] = c4d.DESC_ANIMATE_OFF # Disable animation option
    bc[c4d.DESC_SHADERLINKFLAG] = True
    if parentGroup is not None: # If there is parent group
        bc[c4d.DESC_PARENTGROUP] = parentGroup # Set parent group
    element = obj.AddUserData(bc) # Add user data
    obj[element] = link # Set user data value
    return element # Return user data field

def SetCurrentFrame(frame, doc):
    """ Changes editor's current frame to  """
    doc.SetTime(c4d.BaseTime(frame,doc.GetFps())) # Set current time to given frame
    doc.ExecutePasses(None, True, True, True, 0) # Animate the current frame of the document
    c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED) # Send a synchronous event message that time has changed
    return

def RemoveTags(obj):
    """ Removes tags of the object  """
    hiddenTags = [c4d.PointTag, c4d.PolygonTag] # Tag types that you dont wan't to delete
    tags = obj.GetTags() # Get tags
    for t in tags: # Iterate through tags
        if type(t) not in hiddenTags: # If not protected tag type
            t.Remove() # Remove tag

def Bake(objects):
    """ Bake function """

    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    fps = doc.GetFps() # Get Frame Rate
    startFrame = doc.GetLoopMinTime().GetFrame(fps) # Get first frame of Preview Range
    endFrame = doc.GetLoopMaxTime().GetFrame(fps) # Get last frame of Preview Range
    desc = c4d.DescID(c4d.DescLevel(c4d.CTpla, c4d.CTpla, 0))

    for i in range(startFrame, endFrame+1): # Iterate through Preview Range

        #
        progress = u.RangeMap(i, startFrame, endFrame + 1, 0, 100, True)
        c4d.StatusSetText("Baking frame %s of %s" % (i,endFrame + 1))
        c4d.StatusSetBar(progress)
        #c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW|c4d.DRAWFLAGS_NO_THREAD|c4d.DRAWFLAGS_STATICBREAK) # Updates the viewport during the script runs -> slows down potential baking speed a lot!
        #

        for obj in objects: # Iterate through objects
            source = obj[1] # Dummy object
            target = obj[2] # Bake object
            PLAtrack = target.FindCTrack(desc) # Try to find CTrack
            if not PLAtrack: # If CTrack does not exists
                PLAtrack = c4d.CTrack(target, desc) # Initialize a PLA track
                target.InsertTrackSorted(PLAtrack) # Insert PLA track to the object
            curve = PLAtrack.GetCurve() # Get Curve of the CTrack
            SetCurrentFrame(i, doc) # Set current frame
            frame = doc.GetTime().GetFrame(fps) # Get current frame
            points = source.GetAllPoints()
            currentTime = c4d.BaseTime(frame, fps) # Get current time
            key = curve.AddKey(currentTime)["key"]
            target.SetAllPoints(points)
            target.Message(c4d.MSG_UPDATE)
            PLAtrack.FillKey(doc, target, key)

def main():
    """ The first function to run """
    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    currentTime = doc.GetTime() # Get current time
    selected = doc.GetActiveObjects(0) # Get selected objects
    doc.StartUndo() # Start recording undos
    #bakedObjects = [] # Initialize a list for collecting baked objects
    objects = [] # Initialize a list for objects
    for s in selected: # Iterate through objects
        dummyObj = DummyObject(s, doc) # Dummy object
        bakeObj = dummyObj.GetClone() # Bake object
        name = s.GetName() # Get object's name
        bakeObj.SetName(name+suffix) # Set baked object's name
        bakeObj.InsertAfter(dummyObj) # Insert object to document
        doc.AddUndo(c4d.UNDOTYPE_NEW, bakeObj) # Add undo command for creating a new object
        doc.ExecutePasses(None, True, True, True, 0) # Animate the current frame of the document
        RemoveTags(bakeObj) # Remove tags of the object
        objects.append([s, dummyObj, bakeObj]) # Put object array to objects list
    Bake(objects) # Bake the object
    CopyTags(objects) # Restore tags
    DisableTags(objects) # Disable dynamics tags
    RemoveDummys(objects) # Remove dummy objects

    doc.SetTime(currentTime) # Set current time to back
    doc.ExecutePasses(None, True, True, True, 0) # Animate the current frame of the document
    c4d.GeSyncMessage(c4d.EVMSG_TIMECHANGED) # Send a synchronous event message that time has changed

    for x in reversed(objects):
        MoveToFirst(x[2], doc) # Sort

    doc.EndUndo() # Stop recording undos
    c4d.EventAdd() # Refresh Cinema 4D
    c4d.StatusClear() # Clear status

# Execute main()
if __name__=='__main__':
    main()