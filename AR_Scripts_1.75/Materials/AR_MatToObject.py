"""
AR_MatToObject

Author: Arttu Rautio (aturtur)
Website: http://aturtur.com/
Name-US: AR_MatToObject
Version: 1.0.1
Description-US: Puts material(s) to object(s) with same name

Written for Maxon Cinema 4D R25.010
Python version 3.9.1

Change log:
1.0.1 (24.03.2022) - Updated for R25
"""

# Libraries
import c4d
from c4d import gui

# Functions
def GetNextObject(op):
    if op==None:
        return None
    if op.GetDown():
        return op.GetDown()
    while not op.GetNext() and op.GetUp():
        op = op.GetUp()
    return op.GetNext()

def InsertMaterialTag(op, m):
    tag = c4d.BaseTag(5616) # Initialize a material tag
    tag[c4d.TEXTURETAG_MATERIAL] = m # Assign material to the material tag
    tag[c4d.TEXTURETAG_PROJECTION] = 6 #UVW Mapping
    op.InsertTag(tag) # Insert tag to the object
    doc.AddUndo(c4d.UNDOTYPE_NEW, tag) # Record undo for adding tag

def MatsToObjsWithSameName(op, m, selection, doc):
    if op is None:
        return
    while op:
        if selection:
            if op.GetName() == m.GetName(): # If there are object
                if op.GetBit(c4d.BIT_ACTIVE): # If object is selected
                    InsertMaterialTag(op, m) # Insert material tag to selected object
        else:
            if op.GetName() == m.GetName(): # If there are object
                InsertMaterialTag(op, m) # Insert material tag to the object
        op = GetNextObject(op)
    return True

def main():
    doc.StartUndo() # Start recording undos
    selection = doc.GetActiveObjects(0) # Get active objects
    materials = doc.GetMaterials() # Get all materials
    startObject = doc.GetFirstObject() # Get the first object of the document
    for m in materials: # Iterate through materials
        MatsToObjsWithSameName(startObject, m, selection, doc) # Run the main function            
    doc.EndUndo() # Stop recording undos
    c4d.EventAdd() # Refresh Cinema 4D
        
# Execute main()
if __name__=='__main__':
    main()