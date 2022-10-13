############################################################
# Name: Download Attachments
# Description: Download Attachments script to associate with custom script tool
# Author: Esri Geodatabase Team
#Use: Sample Script Only
############################################################
#import modules
import arcpy
import os, sys

#This script is only a sample script of how to download attachments from a single feature class.
#It will be linked to a script tool for user input.
#Get Tool parameters
#Get the feature class to download attachments
fc = arcpy.GetParameterAsText(0)
#fc = r"C:\Blogs\DownloadAttachments\Download_Attach_PYTH\Download_Attach_PYTH.gdb\Airports"
outFolder = arcpy.GetParameterAsText(1)
#outFolder = r"C:\Blogs\DownloadAttachments\Downloaded_Images"
checkBox = arcpy.GetParameterAsText(2)
#checkBox = "true"
fieldName = arcpy.GetParameterAsText(3)
#fieldName = "Code"

#Verify that the selected feature class has attachments, if not, exit the script
#Script tool will use similar code below to verify attachments before running the tool.
workSpace = arcpy.Describe(fc).path
relclass = arcpy.Describe(fc).relationshipClassNames
try:
    if relclass:
        relclassPath = (f"{workSpace}\\{relclass[0]}")
        relclassAtt = arcpy.Describe(relclassPath).isAttachmentRelationship
        #Attach Table (attTab) will be used with a cursor to get each row of attachments from the Blob field, etc.
        attTab = arcpy.Describe(relclassPath).destinationClassNames
        #Get path for the ATTACH table
        attTabPath = (f"{workSpace}\\{attTab[0]}")
    else:
        #print("FC does not have an Attachment Relationship Class")
        arcpy.AddError("Feature class is not an attachment relationship class")
        sys.exit()
    #If feature class has attachments, then access the ATTACH table.
    attNum = arcpy.GetCount_management(attTabPath)
    attNumstr = str(attNum)
    if int(attNumstr) != 0:
        fldBLOB = 'DATA'
        fldAttName = 'ATT_NAME'
    else:
        #print("FC also does not have any attachments")
        arcpy.AddError("Feature class has no attachments to download")
        sys.exit()

    if checkBox == 'true':
        #if checkBox is checked, this will extract images from the ATTACH table
        #using a field for sub-folders - check for existing sub-folders and create as needed.
        #print("Checkbox is checked")

        #Tool will filter field names from selected feature class using either the ObjectID or GlobalID
        #It appears that older feature classes do not have a GlobalId when they were enabled for attachments. Who knew?
        fcFieldNames = []
        attFldNames = []
        fcFields = arcpy.ListFields(fc)
        for fcFlds in fcFields:
            fcFieldNames.append(fcFlds.name)
        attachFlds = arcpy.ListFields(attTabPath)
        for attFlds in attachFlds:
            attFldNames.append(attFlds.name)
        if not 'GlobalID' in fcFieldNames:
            fcID = 'OBJECTID'
        else:
            fcID = 'GlobalID'
        if not 'REL_GLOBALID' in attFldNames:
            attID = 'REL_OBJECTID'
        else:
            attID = 'REL_GLOBALID'

        with arcpy.da.SearchCursor(fc, [fieldName, fcID]) as fcCursor:
            for row in fcCursor:
                subName = row[0]
                featureID = row[1]
                with arcpy.da.SearchCursor(attTabPath, [attID, "DATA", "ATT_NAME"]) as attCursor:
                    for rows in attCursor:
                        relID = rows[0]
                        binaryRep = rows[1]
                        fileName = rows[2]
                        if featureID == relID:
                            newfldr = (f"{outFolder}\\{subName}")
                            if not os.path.exists(newfldr):
                                os.makedirs(newfldr)
                                picPath = (f"{newfldr}\\{fileName}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del fileName
                                f.close
                            else:
                                picPath = (f"{newfldr}\\{fileName}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del fileName
                                f.close
        arcpy.AddMessage("Extracted attachments to subfolders")
    else:
        #The else part will extract all the images from the ATTACH table to just one output folder
        #print("Checkbox is unchecked")
        with arcpy.da.SearchCursor(attTabPath,[fldBLOB,fldAttName]) as picCursor:
            for row in picCursor:
                binaryRep = row[0]
                fileName = row[1]
                picPath = (f"{outFolder}\\{fileName}")
                f = open(picPath, 'wb')
                f.write(binaryRep.tobytes())
            del binaryRep
            del fileName
            f.close
        arcpy.AddMessage("Extracting Attachments")
    arcpy.SetParameterAsText(4, outFolder)
except:
    # By default any other errors will be caught here
    e = sys.exc_info()[1]
    arcpy.AddError(e.args[0])
    print(e.args[0])