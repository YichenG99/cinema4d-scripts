"""
AR_NodeLineUpH

Author: Arttu Rautio (aturtur)
Website: http://aturtur.com/
Name-US: AR_NodeLineUpH
Version: 1.0.3
Description-US: Lines up selected graph nodes horizontally, supports Xpresso and Redshift

Notice: Make sure the Xpresso tag or the Redshift material is selected when using the script!

Written for Maxon Cinema 4D R25.010
Python version 3.9.1

To Do:
    > Add keyboard modification to vertical alignment (top, _middle_, bottom)

Change log:
1.0.2 (19.10.2023) - Update for Cinema 4D 2024
1.0.2 (07.10.2021) - Updated for R25
1.0.1 (17.02.2021) - Alt modifier: The rightmost node rules
"""

# Libraries
import c4d
try:
    import redshift
except:
    pass
from operator import attrgetter
from c4d import utils as u

# Classes
class nodeObject(object):
    def __init__(self, obj, px, py, sx, sy):
        self.node = obj # Node object
        self.px = px # X position
        self.py = py # Y position
        self.sx = sx # X scale
        self.sy = sy # Y scale

# Functions
def GetKeyMod():
    bc = c4d.BaseContainer() # Initialize a base container
    keyMod = "None" # Initialize a keyboard modifier status
    if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD,c4d.BFM_INPUT_CHANNEL,bc):
        if bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QSHIFT:
            if bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QCTRL: # Ctrl + Shift
                if bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QALT: # Alt + Ctrl + Shift
                    keyMod = 'Alt+Ctrl+Shift'
                else: # Shift + Ctrl
                    keyMod = 'Ctrl+Shift'
            elif bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QALT: # Alt + Shift
                keyMod = 'Alt+Shift'
            else: # Shift
                keyMod = 'Shift'
        elif bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QCTRL:
            if bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QALT: # Alt + Ctrl
                keyMod = 'Alt+Ctrl'
            else: # Ctrl
                keyMod = 'Ctrl'
        elif bc[c4d.BFM_INPUT_QUALIFIER] & c4d.QALT: # Alt
            keyMod = 'Alt'
        else: # No keyboard modifiers used
            keyMod = 'None'
        return keyMod

def DistributeNodes(nodeMaster, keyMod):
    nodes = [] # Initialize a list
    root = nodeMaster.GetRoot() # Get node master root
    for node in root.GetChildren(): # Iterate through nodes
        if node.GetBit(c4d.BIT_ACTIVE): # If node is selected
            bc  = node.GetDataInstance() # Get copy of base container
            bsc = bc.GetContainer(c4d.ID_SHAPECONTAINER) # Get copy of shape container
            bcd = bsc.GetContainer(c4d.ID_OPERATORCONTAINER) # Get copy of operator container
            px  = bcd.GetReal(100) # Get x position
            py  = bcd.GetReal(101) # Get y position
            sx  = bcd.GetReal(108) # Get x scale
            sy  = bcd.GetReal(109) # Get y scale
            nodes.append(nodeObject(node, px, py, sx, sy)) # Create nodeObject and add it to the list

    if nodes: # If there is nodes
        if (keyMod == "Alt") or (keyMod == "Alt+Shift"):
            firstNode = max(nodes, key=attrgetter('px')) # Get the node with the maximum x position value
            nodes.sort(key=attrgetter('px')) # Sort nodes by x position
            nodes.reverse()
            fpos = firstNode.px # Get first position
        else:
            firstNode = min(nodes, key=attrgetter('px')) # Get the node with the minimum x position value
            nodes.sort(key=attrgetter('px')) # Sort nodes by x position
            fpos = firstNode.px + firstNode.sx # Get first position
        count = len(nodes) # Get count of nodes
        r = fpos # Initialize a r variable
    helper = 0 # Initialize a helper variable
    nodeMaster.AddUndo() # Add undo for changing nodes

    if (keyMod == "None") or (keyMod == "Alt"):
        gap = 50
    elif (keyMod == "Shift") or (keyMod == "Alt+Shift"):
        gap = float(c4d.gui.InputDialog("Gap size", 50))

    for i in range(0, len(nodes)): # Iterate through collected nodes
        node=  nodes[i].node # Get node
        bc  = node.GetDataInstance() # Get base container
        bsc = bc.GetContainerInstance(c4d.ID_SHAPECONTAINER) # Get shape container
        bcd = bsc.GetContainerInstance(c4d.ID_OPERATORCONTAINER) # Get operator container

        if i != 0: # Not first node
            s = nodes[i].sx # Get node length
            tAnchor = nodes[i].sy / 2.0
            sAnchor = (firstNode.py + (firstNode.sy / 2.0))
            p = (sAnchor - tAnchor)

            if (keyMod == "Alt+Shift") or (keyMod == "Alt"):
                r = r - s - gap
            else:
                r = r + gap + helper # Calculate node position

            helper = s # Set helper
            bcd.SetReal(100, r) # Set x position
            bcd.SetReal(101, p) # Set y position

def main():
    doc = c4d.documents.GetActiveDocument() # Get active document
    bc = c4d.BaseContainer() # Initialize a base container
    keyMod = GetKeyMod() # Get keymodifier
    doc.StartUndo() # Start recording undos
    materials = doc.GetMaterials() # Get materials
    selection = doc.GetSelection() # Get active selection
    #try: # Try to execute following script
    # Xpresso
    for s in selection: # Iterate through selection
        if type(s).__name__ == "XPressoTag": # If operator is xpresso tag
            xpnm = s.GetNodeMaster() # Get node master
            DistributeNodes(xpnm, keyMod) # Run the main function
    for m in materials: # Iterate through materials
        if m.GetBit(c4d.BIT_ACTIVE): # If material is selected
            rsnm = redshift.GetRSMaterialNodeMaster(m) # Get Redshift material node master
            DistributeNodes(rsnm, keyMod) # Run the main function
#except: # Otherwise
        #pass # Do nothing
    doc.EndUndo() # Stop recording undos
    c4d.EventAdd() # Refresh Cinema 4D

# Execute main()
if __name__=='__main__':
    main()