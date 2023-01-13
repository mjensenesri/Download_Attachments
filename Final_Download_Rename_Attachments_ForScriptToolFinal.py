############################################################
# Name: Download Attachments
# Description: Download Attachments script to associate with custom script tool
# Author: Esri Geodatabase Team
# Use: Sample Script Only
############################################################
#import modules
import arcpy
import os, sys
import pathlib

#This is a sample script of how to download attachments from a single feature class.
#Optionally, the user can rename the exported files using field values from the enabled feature class.
#It will be linked to a script tool for user input.
#Get Tool parameters
#Get the feature class to download attachments
fc = arcpy.GetParameterAsText(0)
#fc = r"C:\Blogs\DownloadAttachments\Download_Attach_PYTH\Download_Attach_PYTH.gdb\Airports"
outFolder = arcpy.GetParameterAsText(1)
#outFolder = r"C:\Blogs\DownloadAttachments\Downloaded_Images"
SubFolderCheckBox = arcpy.GetParameterAsText(2)
#SubFolderCheckBox = "false"
SubfieldName = arcpy.GetParameterAsText(3)
#SubfieldName = "Code"
RenameCheckBox = arcpy.GetParameterAsText(4)
#RenameCheckBox = "true"
getFields = arcpy.GetParameterAsText(5)
#fieldList = ["NAME", "TEST"]
fieldList = []
fieldNameList = getFields.split(";")
for fldName in fieldNameList:
    fieldList.append(fldName)
AddPrefixCheckBox = arcpy.GetParameterAsText(6)
#AddPrefixCheckBox = "true"
AddSuffixCheckBox = arcpy.GetParameterAsText(7)
#AddSuffixCheckBox = "true"

#Verify that the selected feature class has attachments, if not, exit the script
#Script tool will use similar code below to verify attachments before running the tool.
workSpace = arcpy.Describe(fc).path
relclass = arcpy.Describe(fc).relationshipClassNames
relclassPath = (f"{workSpace}\\{relclass[0]}")
relclassAtt = arcpy.Describe(relclassPath).isAttachmentRelationship
try:
    if relclassAtt:
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

    # Tool will filter field names from selected feature class using either the ObjectID or GlobalID
    # It appears that older feature classes do not have a GlobalId when they were enabled for attachments. Who knew?
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
        attRelID = 'REL_OBJECTID'
    else:
        attRelID = 'REL_GLOBALID'

    SubFieldsList = [SubfieldName, fcID]
    RenameFieldsList = fieldList

    #Export attachments with original file name into subfolders with selected field value only. - Verified
    if SubFolderCheckBox == 'true' and RenameCheckBox == 'false' and AddPrefixCheckBox == 'false' and AddSuffixCheckBox == 'false':
        with arcpy.da.SearchCursor(fc, [SubfieldName, fcID]) as fcCursor:
            for row in fcCursor:
                subName = row[0]
                featureID = row[1]
                with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                    for rows in attCursor:
                        relID = rows[0]
                        binaryRep = rows[1]
                        origFileName = rows[2]
                        if featureID == relID:
                            newfldr = (f"{outFolder}\\{subName}")
                            if not os.path.exists(newfldr):
                                os.makedirs(newfldr)
                                picPath = (f"{newfldr}\\{origFileName}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del origFileName
                                f.close
                            else:
                                picPath = (f"{newfldr}\\{origFileName}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del origFileName
                                f.close
        arcpy.AddMessage("Extracted attachments to subfolders")

    # Add prefix to existing attachment filenames and export to output folder only. - Verified
    elif SubFolderCheckBox == 'false' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'true' and AddSuffixCheckBox == 'false':
        PreRenameList = SubFieldsList + RenameFieldsList
        #print(f"SubRename List: {PreRenameList}")
        numPreRename = len(PreRenameList)
        #print(numPreRename)
        if numPreRename == 3:
            with arcpy.da.SearchCursor(fc, PreRenameList) as fcCursor:
                for pre in fcCursor:
                    subName = pre[0]
                    featureID = pre[1]
                    prefilename = (f"{pre[2]}")
                    #print(f"prefilename for 1 field is: {prefilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            fileName = rows[2]
                            if featureID == relID and os.path.exists(outFolder):
                                picPath = (f"{outFolder}\\{prefilename}_{fileName}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del fileName
                                f.close

            arcpy.AddMessage(f"Extracted attachments to {outFolder} with prefix added to original name")
        else:
            arcpy.AddError("Only one field can be used for Prefix renaming")

    # Add prefix to existing attachment filenames and export to subfolders by field value name. - Verified
    elif SubFolderCheckBox == 'true' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'true' and AddSuffixCheckBox == 'false':
        PreRenameList = SubFieldsList + RenameFieldsList
        #print(f"SubRename List: {PreRenameList}")
        numPreRename = len(PreRenameList)
        #print(numPreRename)
        if numPreRename == 3:
            with arcpy.da.SearchCursor(fc, PreRenameList) as fcCursor:
                for pre in fcCursor:
                    subName = pre[0]
                    featureID = pre[1]
                    prefilename = (f"{pre[2]}")
                    print(f"prefilename for 1 field is: {prefilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            fileName = rows[2]
                            if featureID == relID:
                                newfldr = (f"{outFolder}\\{subName}")
                                if not os.path.exists(newfldr):
                                    os.makedirs(newfldr)
                                    picPath = (f"{newfldr}\\{prefilename}_{fileName}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
                                else:
                                    picPath = (f"{newfldr}\\{prefilename}_{fileName}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
            arcpy.AddMessage("Extracted attachments to subfolders with prefix added to original name")
        else:
            arcpy.AddError("Only one field can be used for Prefix renaming")

    # Add suffix to existing attachment filenames and export to output folder only.  - Verified
    elif SubFolderCheckBox == 'false' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'false' and AddSuffixCheckBox == 'true':
        PreRenameList = SubFieldsList + RenameFieldsList
        #print(f"SubRename List: {PreRenameList}")
        numPreRename = len(PreRenameList)
        #print(numPreRename)
        if numPreRename == 3:
            with arcpy.da.SearchCursor(fc, PreRenameList) as fcCursor:
                for pre in fcCursor:
                    subName = pre[0]
                    featureID = pre[1]
                    suffilename = (f"{pre[2]}")
                    #print(f"prefilename for 1 field is: {prefilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            attFileName = rows[2]
                            fileNameOnly = pathlib.Path(attFileName).stem
                            file_extension = pathlib.Path(attFileName).suffix
                            #print(fileNameOnly)
                            #print(file_extension)
                            if featureID == relID and os.path.exists(outFolder):
                                picPath = (f"{outFolder}\\{fileNameOnly}_{suffilename}{file_extension}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del attFileName
                                f.close

            arcpy.AddMessage(f"Extracted attachments to {outFolder} with suffix added to original name")
        else:
            arcpy.AddError("Only one field can be used for Suffix renaming")

        # Add suffix to existing attachment filenames and export to subfolders by field value name. - Verified
    elif SubFolderCheckBox == 'true' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'false' and AddSuffixCheckBox == 'true':
        PreRenameList = SubFieldsList + RenameFieldsList
        # print(f"SubRename List: {PreRenameList}")
        numPreRename = len(PreRenameList)
        # print(numPreRename)
        if numPreRename == 3:
            with arcpy.da.SearchCursor(fc, PreRenameList) as fcCursor:
                for pre in fcCursor:
                    subName = pre[0]
                    featureID = pre[1]
                    suffilename = (f"{pre[2]}")
                    #print(f"suffilename for 1 field is: {suffilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            fileName = rows[2]
                            fileNameOnly = pathlib.Path(fileName).stem
                            file_extension = pathlib.Path(fileName).suffix
                            if featureID == relID:
                                newfldr = (f"{outFolder}\\{subName}")
                                if not os.path.exists(newfldr):
                                    os.makedirs(newfldr)
                                    picPath = (f"{newfldr}\\{fileNameOnly}_{suffilename}{file_extension}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
                                else:
                                    picPath = (f"{newfldr}\\{fileNameOnly}_{suffilename}{file_extension}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
            arcpy.AddMessage("Extracted attachments to subfolders with suffix added to original name")
        else:
            arcpy.AddError("Only one field can be used for Prefix renaming")

    # Add a prefix value and suffix value to existing attachment filenames and export to subfolders using 2 field value names. - Verified
    elif SubFolderCheckBox == 'true' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'true' and AddSuffixCheckBox == 'true':
        PreSufRenameList = SubFieldsList + RenameFieldsList
        # print(f"SubRename List: {PreRenameList}")
        numPreSufRename = len(PreSufRenameList)
        # print(numPreRename)
        if numPreSufRename == 4:
            with arcpy.da.SearchCursor(fc, PreSufRenameList) as fcCursor:
                for presuf in fcCursor:
                    subName = presuf[0]
                    featureID = presuf[1]
                    prefilename = (f"{presuf[2]}")
                    suffilename = (f"{presuf[3]}")
                    #print(f"prefilename for 1st field is: {prefilename} -- suffilename for 2nd field is: {suffilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            fileName = rows[2]
                            fileNameOnly = pathlib.Path(fileName).stem
                            file_extension = pathlib.Path(fileName).suffix
                            if featureID == relID:
                                newfldr = (f"{outFolder}\\{subName}")
                                if not os.path.exists(newfldr):
                                    os.makedirs(newfldr)
                                    picPath = (f"{newfldr}\\{prefilename}_{fileNameOnly}_{suffilename}{file_extension}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
                                else:
                                    picPath = (f"{newfldr}\\{prefilename}_{fileNameOnly}_{suffilename}{file_extension}")
                                    # print(f"{featureID} = {relID}")
                                    f = open(picPath, 'wb')
                                    f.write(binaryRep.tobytes())
                                    del binaryRep
                                    del fileName
                                    f.close
            arcpy.AddMessage("Extracted attachments to subfolders with prefix and suffix added to original name")
        else:
            arcpy.AddError("Two fields are expected for renaming original filenames with an appended prefix and suffix")

    # Rename attachment files based on one or more fieldnames into a subfolder - Verified
    elif SubFolderCheckBox == 'true' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'false' and AddSuffixCheckBox == 'false':
        #print("Print1")
        SubRenameList = SubFieldsList + RenameFieldsList
        print(f"SubRename List: {SubRenameList}")
        numSubRename = len(SubRenameList)
        #print(numSubRename)
        attSelect = 'fcID = attID'

        with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME", "ATTACHMENTID"]) as attCursor:
            for atts in attCursor:
                relID = atts[0]
                binaryRep = atts[1]
                attfileName = atts[2]
                attID = atts[3]
                file_extension = pathlib.Path(attfileName).suffix
                with arcpy.da.SearchCursor(fc, SubRenameList) as subNameCursor:
                    for recs in subNameCursor:
                        subName = recs[0]
                        featureID = recs[1]
                        if numSubRename == 3:
                            newfilename = (f"{recs[2]}")
                            #print(f"newfilename for 1 fields is: {newfilename}")
                        elif numSubRename == 4:
                            newfilename = (f"{recs[2]}_{recs[3]}")
                            #print(f"newfilename for 2 fields is: {newfilename}")
                        elif numSubRename == 5:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}")
                            #print(f"newfilename for 3 fields is: {newfilename}")
                        elif numSubRename == 6:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}_{recs[5]}")
                            #print(f"newfilename for 4 fields is: {newfilename}")
                        elif numSubRename == 7:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}_{recs[5]}_{recs[6]}")
                            print(f"newfilename for 5 fields is: {newfilename}")
                        if featureID == relID:
                            newfldr = (f"{outFolder}\\{subName}")
                            if not os.path.exists(newfldr):
                                os.makedirs(newfldr)
                                fullName = (f"{newfilename}_{attID}{file_extension}")
                                print(f"FULLNAME is {fullName}")
                                newPicName = (f'{newfldr}\\{fullName}')
                                #print(f"{featureID} = {relID}")
                                f = open(newPicName, 'wb')
                                f.write(binaryRep.tobytes())
                                f.close

                            else:
                                fullName = (f"{newfilename}_{attID}{file_extension}")
                                newPicName = (f'{newfldr}\\{fullName}')
                                newPicName2 = (f'{newfldr}\\{fullName}')
                                #print(f"newPicName is: {newPicName2}")
                                f = open(newPicName2, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del attfileName
                                f.close

        arcpy.AddMessage(f"Extracted attachments to subfolders with renamed files from selected fields and appended attachment ID")

        # Rename attachment files based on one or more fieldnames exported into output folder only - Verified
    elif SubFolderCheckBox == 'false' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'false' and AddSuffixCheckBox == 'false':
        # print("Print1")
        SubRenameList = SubFieldsList + RenameFieldsList
        print(f"SubRename List: {SubRenameList}")
        numSubRename = len(SubRenameList)
        # print(numSubRename)
        attSelect = 'fcID = attID'

        with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME", "ATTACHMENTID"]) as attCursor:
            for atts in attCursor:
                relID = atts[0]
                binaryRep = atts[1]
                attfileName = atts[2]
                attID = atts[3]
                file_extension = pathlib.Path(attfileName).suffix
                with arcpy.da.SearchCursor(fc, SubRenameList) as subNameCursor:
                    for recs in subNameCursor:
                        subName = recs[0]
                        featureID = recs[1]
                        if numSubRename == 3:
                            newfilename = (f"{recs[2]}")
                            # print(f"newfilename for 1 fields is: {newfilename}")
                        elif numSubRename == 4:
                            newfilename = (f"{recs[2]}_{recs[3]}")
                            # print(f"newfilename for 2 fields is: {newfilename}")
                        elif numSubRename == 5:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}")
                            # print(f"newfilename for 3 fields is: {newfilename}")
                        elif numSubRename == 6:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}_{recs[5]}")
                            # print(f"newfilename for 4 fields is: {newfilename}")
                        elif numSubRename == 7:
                            newfilename = (f"{recs[2]}_{recs[3]}_{recs[4]}_{recs[5]}_{recs[6]}")
                            #print(f"newfilename for 5 fields is: {newfilename}")
                        if featureID == relID:
                            fullName = (f"{newfilename}_{attID}{file_extension}")
                            #print(f"FULLNAME is {fullName}")
                            newPicName = (f'{outFolder}\\{fullName}')
                            f = open(newPicName, 'wb')
                            f.write(binaryRep.tobytes())
                            f.close

            arcpy.AddMessage(f"Extracted attachments to {outFolder} folder with images renamed with selected field values appended with attachment ID")

    # Add a prefix value and suffix value to existing attachment filenames and export to subfolders using 2 field value names. - Verified
    elif SubFolderCheckBox == 'false' and RenameCheckBox == 'true' and AddPrefixCheckBox == 'true' and AddSuffixCheckBox == 'true':
        PreSufRenameList = SubFieldsList + RenameFieldsList
        # print(f"SubRename List: {PreRenameList}")
        numPreSufRename = len(PreSufRenameList)
        # print(numPreRename)
        if numPreSufRename == 4:
            with arcpy.da.SearchCursor(fc, PreSufRenameList) as fcCursor:
                for presuf in fcCursor:
                    subName = presuf[0]
                    featureID = presuf[1]
                    prefilename = (f"{presuf[2]}")
                    suffilename = (f"{presuf[3]}")
                    # print(f"prefilename for 1st field is: {prefilename} -- suffilename for 2nd field is: {suffilename}")
                    with arcpy.da.SearchCursor(attTabPath, [attRelID, "DATA", "ATT_NAME"]) as attCursor:
                        for rows in attCursor:
                            relID = rows[0]
                            binaryRep = rows[1]
                            fileName = rows[2]
                            fileNameOnly = pathlib.Path(fileName).stem
                            file_extension = pathlib.Path(fileName).suffix
                            if featureID == relID:
                                picPath = (f"{outFolder}\\{prefilename}_{fileNameOnly}_{suffilename}{file_extension}")
                                # print(f"{featureID} = {relID}")
                                f = open(picPath, 'wb')
                                f.write(binaryRep.tobytes())
                                del binaryRep
                                del fileName
                                f.close

            arcpy.AddMessage(f"Extracted attachments to {outFolder} folder with prefix and suffix added to original name")
        else:
            arcpy.AddError("Two fields are expected for renaming original filenames with an appended prefix and suffix")

    else:
        # The else part will extract all the images from the ATTACH table to just one output folder
        # print("Checkbox is unchecked")
        with arcpy.da.SearchCursor(attTabPath, [fldBLOB, fldAttName]) as picCursor:
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
    arcpy.SetParameterAsText(8, outFolder)
except:
    # By default any other errors will be caught here
    e = sys.exc_info()[1]
    arcpy.AddError(e.args[0])
    print(e.args[0])
