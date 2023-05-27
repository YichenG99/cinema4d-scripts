"""
AR_MatConsolidateTags

Author: Arttu Rautio (aturtur)
Website: http://aturtur.com/
Name-US: AR_MatConsolidateTags
Version: 1.0.1
Description-US: Consolidates different polygon selections together that uses same materials. Messes up material projections! Select object(s) and run the script.

Written for Maxon Cinema 4D R25.010
Python version 3.9.1

Change log:
1.0.1 (24.03.2022) - Updated for R25
"""

# Libraries
import c4d

# Functions
def GetNextObject(op):
    if op == None:
        return None
    if op.GetDown():
        return op.GetDown()
    while not op.GetNext() and op.GetUp():
        op = op.GetUp()
    return op.GetNext()

def IterateHierarchy(op):
    if op is None:
        return
    while op:
        ConsolidateMaterialSelections(op)
        op = GetNextObject(op)
    return

def ConsolidateMaterialSelections(s):
    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    selectionTags = [] # Initialize list for selection tags
    materialTags = [] # Initialize list for material tags
    materials = [] # Initialize list for materials
    tags = s.GetTags() # Get object's tags

    # Collect information
    for t in tags: # Iterate through tags
        #print t.GetType(), t.GetName()
        if t.GetType() == 5673: # If tag is a selection tag
            selectionTags.append(t) # Add tag to selection tags list
        elif t.GetType() == 5616: # If tag is a material tag
            materialTags.append(t) # Add tag to material tags list
            if t[c4d.TEXTURETAG_MATERIAL] not in materials: # If material is not already in materials
                materials.append(t[c4d.TEXTURETAG_MATERIAL]) # Add material to materials list
        else: # Otherwise
            pass # Do nothing

    # Action
    for m in materials: # Iterate through materials
        materialTag = c4d.BaseTag(5616) # Initialize a material tag
        selectionTag = c4d.SelectionTag(c4d.Tpolygonselection) # Initialize a selection tag
        selectionTag.SetName(m.GetName()+"_sel") # Set selection tag's name
        for mt in materialTags: # Iterate through material tags
            doc.AddUndo(c4d.UNDOTYPE_DELETE, s) # Add undo for deleting tags
            if mt[c4d.TEXTURETAG_MATERIAL] == m: # If material tag uses material
                for st in selectionTags: # Iterate through selection tags
                    if mt[c4d.TEXTURETAG_RESTRICTION] == st.GetName(): # If material tag is using this selection tag
                        fromSelect = st.GetBaseSelect() # Get old selection
                        toSelect = selectionTag.GetBaseSelect() # Get selection
                        toSelect.Merge(fromSelect) # Add to selection
                    st.Remove() # Remove old selection tag
                mt.Remove() # Remove old material tag
        s.InsertTag(selectionTag) # Insert selection tag to the object
        s.InsertTag(materialTag) # Insert new material tag
        doc.AddUndo(c4d.UNDOTYPE_NEW, s) # Add undo for new tags
        materialTag[c4d.TEXTURETAG_MATERIAL] = m # Set material
        materialTag[c4d.TEXTURETAG_RESTRICTION] = selectionTag.GetName() # Set selection

def main():
    doc = c4d.documents.GetActiveDocument() # Get active Cinema 4D document
    doc.StartUndo() # Start recording undos
    selection = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN) # Get selected objects
    if len(selection) != 0: # If object selection
        for s in selection: # Iterate through selection
            ConsolidateMaterialSelections(s) # Run the function    
    else: # Otherwise
        IterateHierarchy(doc.GetFirstObject()) # Iterate through all objects
    doc.EndUndo() # Stop recording undos
    c4d.EventAdd() # Refresh Cinema 4D

# Execute main()
if __name__=='__main__':
    main()