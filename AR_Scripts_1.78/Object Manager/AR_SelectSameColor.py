"""
AR_SelectSameColor

Author: Arttu Rautio (aturtur)
Website: http://aturtur.com/
Name-US: AR_SelectSameColor
Version: 1.0.1
Description-US: Selects object(s) with same object color that active object has

Written for Maxon Cinema 4D R25.010
Python version 3.9.1

Change log:
1.0.1 (18.08.2022) - R25 support
"""
# Libraries
import c4d

# Functions
def GetNextObject(op):
    if op==None:
        return None
    if op.GetDown():
        return op.GetDown()
    while not op.GetNext() and op.GetUp():
        op = op.GetUp()
    return op.GetNext()
 
def IterateHierarchy(op, color):
    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    if op is None:
        return
    while op:
        if op[c4d.ID_BASEOBJECT_COLOR] == color: # If object color is same as reference color
            op.SetBit(c4d.BIT_ACTIVE) # Select object
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, op) # Add undo command for selecting object
        op = GetNextObject(op) # Get next object
    return True

def main():
    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    doc.StartUndo() # Start recording undos
    try: # Try to execute following script
        active_object = doc.GetActiveObject() # Get active object
        reference_color = active_object[c4d.ID_BASEOBJECT_COLOR] # Object color
        start_object = doc.GetFirstObject() # Get first object
        IterateHierarchy(start_object, reference_color) # Do the thing
    except: # If something went wrong
        pass # Do nothing
    doc.EndUndo() # Stop recording undos
    c4d.EventAdd() # Refresh Cinema 4D
  
# Execute main()
if __name__=='__main__':
    main()