"""
PySAAT - Python-based segmentation accuracy analysis toolbox 
Created on Mon 27 Nov 12:00:00 2023
@authors:
"""
import subprocess
import tkinter as tk					 
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from time import process_time
import os
import geopandas as gpd
import pandas as pd
import time
import math
import re
import matplotlib.pyplot as plt
from sqlalchemy.engine import URL
from sqlalchemy import create_engine
import sqlalchemy as sa

def runPreprocess():
    def startProcess():        
        t1_start = process_time() 
        intersection = pd.DataFrame(columns = ['sampleno','samparea', \
                                               'segmentno','segarea', \
                                                   'intersectarea', 'distance'])
        progressLabel.config(text='Pre-process is running, please wait ...      ')
        bar2Text = 'Importing '+ str(sNCounter) + '. segmentation ...'  
        progressLabel2.config(text = bar2Text)
        my_progress['value'] = 0
        my_progress.update_idletasks()
        time.sleep(1)
        for i in range(len(sam_gdf)):
            updateText = str(i) + '/' + str(len(sam_gdf)) + ' ...' 
            progressLabel4.config(text=updateText)
            c_s = sam_gdf['geometry'].iloc[i].bounds
            subsegment = segment_gdf.cx[c_s[0]:c_s[2],c_s[1]:c_s[3]]             
            for j in range(len(subsegment)):
                result = gpd.overlay(sam_gdf.iloc[i:i+1],subsegment.iloc[j:j+1],  how='intersection')
                if result.empty == False:
                    sampleno = sam_gdf.iloc[i:i+1].area.index[0] + 1
                    sam_area = sam_gdf['geometry'].iloc[int(sampleno)-1].area
                    sam_cen = sam_gdf['geometry'].iloc[int(sampleno)-1].centroid 
                    segmentno = subsegment.iloc[j:j+1].area.index[0] + 1
                    seg_area = subsegment['geometry'][int(segmentno)-1].area
                    seg_cen = subsegment['geometry'][int(segmentno)-1].centroid
                    dist  = math.sqrt((sam_cen.y-seg_cen.y)**2 + (sam_cen.x-seg_cen.x)**2)
                    area_list = list(result.iloc[0:1].area)
                    intersectarea = area_list[0]

                    new_intersection_row = pd.DataFrame({'sampleno': sampleno, \
                                                        'samparea': sam_area, \
                                                        'segmentno': segmentno, \
                                                            'segarea': seg_area, \
                                                            'intersectarea': intersectarea, \
                                                                'distance': dist}, index=[0])
                    intersection = pd.concat([intersection, new_intersection_row])
            inc = (i+1)*100/len(subsegment)
            my_progress['value'] = inc
            my_progress.update_idletasks()
            time.sleep(1)       
        updateText = str(len(sam_gdf)) + '/' + str(len(sam_gdf))
        progressLabel4.config(text=updateText)        
        intersection.to_pickle(intPath)
        t1_stop = process_time()
        fs = open(prcTime,"w")
        duration = (t1_stop-t1_start)/60
        fs.write("Elapsed time during the process in minutes: %5.2f" % (duration))
        fs.close()
    my_progress['value'] = 0
    my_progress.update_idletasks()
    time.sleep(1)    
    overall_progress['value'] = 0
    overall_progress.update_idletasks()
    time.sleep(1)
    dirPath = e3.get()
    if e2.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please define sample file (.shp) !")
        return   
    sam_gdf = gpd.read_file(e2.get())
    samPath = dirPath + '/sample.pkl'
    sam_gdf.to_pickle(samPath)
    segFileNames= []
    sNCounter = 1
    if segmentationNum.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please define number of segmentation files !")
        return
    sN = int(segmentationNum.get())
    for i in range(sN):
        messageHeader = 'Segmentation ' + str(sNCounter)
        messageText = 'Browse ' + str(sNCounter) + '. segmentation file (.shp)'
        messagebox.showinfo(messageHeader, messageText)
        segFileNames.append(loadSegFile())
        sNCounter = sNCounter + 1   
    sNCounter = 1
    for i in range(sN):
        updateText = str(i) + '/' + str(sN) + ' ...'
        progressLabel5.config(text=updateText)
        segment_gdf = gpd.read_file(segFileNames[i])
        subFolderName = "segmentation" + str(sNCounter)
        subFolder = os.path.join(dirPath,subFolderName) 
        if not os.path.isdir(subFolder):            
            os.makedirs(subFolder)
           
        subFolder = os.path.join(dirPath,subFolderName)
        segPath = subFolder + '/segment.pkl'
        segment_gdf.to_pickle(segPath)
        intPath = subFolder + '/intersect.pkl'
        prcTime = subFolder + '/process_time.txt'
        startProcess()
        incOver = (i+1)*100/sN
        overall_progress['value'] = incOver
        overall_progress.update_idletasks()
        time.sleep(1)
        sNCounter = sNCounter + 1        
    updateText = str(sN) + '/' + str(sN)
    sam_gdf['coords'] = sam_gdf['geometry'].apply(lambda x: x.representative_point().coords[:])
    sam_gdf['coords'] = [coords[0] for coords in sam_gdf['coords']]
    fig3, ax3 = plt.subplots()
    ax3.set_aspect('equal')
    sam_gdf.boundary.plot(ax=ax3, aspect=1, edgecolor='red', linewidth=1)
    i = 1
    for idx, row in sam_gdf.iterrows():
        plt.annotate(text=str(i), xy=row['coords'], horizontalalignment='center', color='blue')
        i = i + 1
    plt.title("All Samples")
    sam3fig = ax3.get_figure()
    sam3figPath = dirPath + '/samples.pdf'
    sam3fig.savefig(sam3figPath)
    progressLabel5.config(text=updateText)    
    progressLabel.config(text='Your files have been successfully imported.  ')    
def runPreprocess_db():    
    def connectMessage():    
        try:
            global url_object
            url_object = URL.create("postgresql+pg8000", database=e10.get(), username=e11.get(), password=e12.get(), host=e13.get(), port=e14.get())
        except:
            messagebox.showerror("Error", "Database connection is not successful.")            
    def checkSampleData():
        try:
            global url_object
            engine = create_engine(url_object)
            with engine.begin() as conn:
                df_sql = pd.read_sql_query(sa.text("SELECT Geometrytype (" + e16.get() + ") FROM " + e15.get() + " WHERE gid = '1';"), conn)
                sonuc = df_sql.iloc[0,0]
                x = re.search("MULTIPOLYGON", sonuc)
                if x:
                    messagebox.showinfo("Connection Info", "Database connection is successful.\nSample data has been ready.")
                else:
                    messagebox.showerror("Error", "Geometry column type is not a polygon in the sample table.")
        except:
            messagebox.showerror("Error", "Geometry column could not be found in the sample table.")
    def checkSegmentData(sNCounter):
        try:            
            iuTitle1 = str(sNCounter) + '. segmentation table' 
            iuPrompt1 = 'Enter table name of the ' + str(sNCounter) + '. segmentation : '
            userInput1 = simpledialog.askstring(title=iuTitle1, prompt=iuPrompt1, initialvalue="segmentation")
            iuTitle2 = str(sNCounter) + '. segmentation column' 
            iuPrompt2 = 'Enter column name of the ' + str(sNCounter) + '. segmentation : '
            userInput2 = simpledialog.askstring(title=iuTitle2, prompt=iuPrompt2, initialvalue="geom")
            global url_object
            engine = create_engine(url_object)
            with engine.begin() as conn:
                df_sql = pd.read_sql_query(sa.text("SELECT Geometrytype (" + userInput2 + ") FROM " + userInput1 + " WHERE gid = '1';"), conn)
                sonuc = df_sql.iloc[0,0]
                x = re.search("MULTIPOLYGON", sonuc)
                if x:
                    messagebox.showinfo("Sample Info", "Your segment data is ready.")                
                else:
                    messagebox.showerror("Error", "A geometry column type is not a polygon.")
        except:
                messagebox.showerror("Error", "A geometry column could not be found.")
        return userInput1, userInput2        
    def startProcess():
        t1_start = process_time() 
        intersection = pd.DataFrame(columns = ['sampleno','samparea', \
                                                'segmentno','segarea', \
                                                    'intersectarea', 'distance'])
        progressLabel.config(text='Pre-process is running, please wait ...')
        bar2Text = 'Importing '+ str(sNCounter) + '. segmentation ...'  
        progressLabel2.config(text = bar2Text)
        my_progress['value'] = 0
        my_progress.update_idletasks()
        time.sleep(1)        
        engine = create_engine(url_object)
        with engine.begin() as conn:
            segment_sql = "SELECT geom FROM " + segmentTable
            segment_gdf = gpd.read_postgis(segment_sql, conn)
            segment_gdf = segment_gdf.rename_geometry('geometry')
            segPath = dirPath + '/segmentation'+ str(sNCounter) + '/segment.pkl'
            segment_gdf.to_pickle(segPath)        
            sample_sql = "SELECT geom FROM " + samTable
            sam_gdf = gpd.read_postgis(sample_sql, conn)
            sam_gdf = sam_gdf.rename_geometry('geometry')
            samPath = dirPath + '/sample.pkl'
            sam_gdf.to_pickle(samPath)
        for i in range(len(sam_gdf)):
            updateText = str(i) + '/' + str(len(sam_gdf)) + ' ...' 
            progressLabel4.config(text=updateText)
            c_s = sam_gdf['geometry'].iloc[i].bounds
            subsegment = segment_gdf.cx[c_s[0]:c_s[2],c_s[1]:c_s[3]]             
            for j in range(len(subsegment)):
                result = gpd.overlay(sam_gdf.iloc[i:i+1],subsegment.iloc[j:j+1],  how='intersection')
                if result.empty == False:
                    sampleno = sam_gdf.iloc[i:i+1].area.index[0] + 1
                    sam_area = sam_gdf['geometry'].iloc[int(sampleno)-1].area
                    sam_cen = sam_gdf['geometry'].iloc[int(sampleno)-1].centroid 
                    segmentno = subsegment.iloc[j:j+1].area.index[0] + 1
                    seg_area = subsegment['geometry'][int(segmentno)-1].area
                    seg_cen = subsegment['geometry'][int(segmentno)-1].centroid
                    dist  = math.sqrt((sam_cen.y-seg_cen.y)**2 + (sam_cen.x-seg_cen.x)**2)
                    area_list = list(result.iloc[0:1].area)
                    intersectarea = area_list[0] 

                    new_intersection_row = pd.DataFrame({'sampleno': sampleno, \
                                                        'samparea': sam_area, \
                                                        'segmentno': segmentno, \
                                                            'segarea': seg_area, \
                                                            'intersectarea': intersectarea, \
                                                                'distance': dist}, index=[0])
                    intersection = pd.concat([intersection, new_intersection_row])
            inc = (i+1)*100/len(subsegment)
            my_progress['value'] = inc
            my_progress.update_idletasks()
            time.sleep(1)       
        updateText = str(len(sam_gdf)) + '/' + str(len(sam_gdf))
        progressLabel4.config(text=updateText)        
        intersection.to_pickle(intPath)
        t1_stop = process_time()
        fs = open(prcTime,"w")
        duration = (t1_stop-t1_start)/60
        fs.write("Elapsed time during the process in minutes: %5.2f" % (duration))
        fs.close()   
    my_progress['value'] = 0
    my_progress.update_idletasks()
    time.sleep(1)    
    overall_progress['value'] = 0
    overall_progress.update_idletasks()
    time.sleep(1)    
    connectMessage()
    checkSampleData()     
    dirPath = e3.get()
    samTable= e15.get()
    segTableNames= []
    segGeomNames= []
    sNCounter = 1
    sN = int(segmentationNum_db.get())
    for i in range(sN):
        ui1, ui2 = checkSegmentData(sNCounter)
        segTableNames.append(ui1)
        segGeomNames.append(ui2)
        sNCounter = sNCounter + 1
    sNCounter = 1
    for i in range(sN):
        updateText = str(i) + '/' + str(sN) + ' ...'
        progressLabel5.config(text=updateText)
        segmentTable = segTableNames[i]
        subFolderName = "segmentation" + str(sNCounter)
        subFolder = os.path.join(dirPath,subFolderName) 
        if not os.path.isdir(subFolder):            
            os.makedirs(subFolder)
        intPath = subFolder + '/intersect.pkl'
        prcTime = subFolder + '/process_time.txt'
        startProcess()
        incOver = (i+1)*100/sN
        overall_progress['value'] = incOver
        overall_progress.update_idletasks()
        time.sleep(1)
        sNCounter = sNCounter + 1
    updateText = str(sN) + '/' + str(sN)
    progressLabel5.config(text=updateText)
    progressLabel.config(text='Your files have been successfully imported.')
def calculateAllIndices():
    if e3.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please define working directory !")
        return   
    dirPath = e3.get()
    if segmentationNum2.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please define number of segmentation directories !")
        return
    sN = int(segmentationNum2.get())
    for i in range(sN):
        k = i+1
        calculateIndex(dirPath,k)
    if sN == 1:
        messagebox.showinfo("PySAAT", "Segmentation accuracy has been calculated.")    
    else:
        messagebox.showinfo("PySAAT", "Segmentation accuracies have been calculated.")        
def plotSegments():
    if e40.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please enter sample no !")
        return   
    samNo = e40.get()
    samNo = int(samNo)
    samIndexNo = samNo-1
    if e41.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please enter segmentation no !")
        return
    segmentationNo = e41.get()
    if e3.index("end") == 0:
        messagebox.showwarning(title="Warning", message="Please define working directory !")
        return   
    dirPath = e3.get()   
    intersectPath = dirPath + '/segmentation' + segmentationNo + '/intersect.pkl'    
    try:
        intersectPath_df  = pd.read_pickle(intersectPath)
    except:
        messagebox.showwarning(title="Warning", message="Segmentation directory is not found !")
        return    
    sample_segments = intersectPath_df.loc[intersectPath_df['sampleno'] == samNo]
    intersectNo = len(sample_segments)    
    samPath = dirPath + '/sample.pkl'
    samPath_df  = pd.read_pickle(samPath)
    sampleLen = len(samPath_df)    
    if samNo > sampleLen or samNo <= 0:
        messagebox.showwarning(title="Warning", message="Please enter a valid sample no !")
        return   
    segPath = dirPath + '/segmentation' + segmentationNo + '/segment.pkl'
    segPath_df  = pd.read_pickle(segPath)     
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    
    samPath_df_org = samPath_df
    samPath_df = samPath_df.iloc[[samIndexNo]]
    samPath_df.boundary.plot(ax=ax, aspect=1, edgecolor='red', linewidth=1, zorder=2)
    for i in range(intersectNo):
        segno = sample_segments['segmentno'].iloc[i]
        segPath_df_temp = segPath_df.iloc[[segno-1]]
        segPath_df_temp.boundary.plot(ax=ax, aspect=1, edgecolor='blue', linewidth=0.25)
    coor = samPath_df_org.iloc[[samIndexNo]].representative_point()
    plt.text(float(coor.geometry.x[samIndexNo]), float(coor.geometry.y[samIndexNo]), str(samIndexNo+1), color='red')
    plt.title("The sample with all intersected segments")
    samfig = ax.get_figure()  
    samfigPath = dirPath + '/segmentation' + segmentationNo + '/sample_segments.pdf'
    samfig.savefig(samfigPath)
    x1=ax.get_xlim()[0]
    x2=ax.get_xlim()[1]
    y1=ax.get_ylim()[0]
    y2=ax.get_ylim()[1]
    fig2, ax2 = plt.subplots()
    ax2.set_aspect('equal')
    ax2.set_xlim(x1,x2)
    ax2.set_ylim(y1,y2)
    samPath_df.boundary.plot(ax=ax2, aspect=1, edgecolor='red', linewidth=1, zorder=2)
    selectMaxSample = sample_segments['intersectarea'].argmax()
    segno = sample_segments['segmentno'].iloc[selectMaxSample]
    segPath_df_temp = segPath_df.iloc[[segno-1]]
    segPath_df_temp.boundary.plot(ax=ax2, aspect=1, edgecolor='blue', linewidth=0.25)
    plt.text(float(coor.geometry.x[samIndexNo]), float(coor.geometry.y[samIndexNo]), str(samIndexNo+1), color='red')
    plt.title("The sample with maximum intersected segment")
    sam2fig = ax2.get_figure()
    sam2figPath = dirPath + '/segmentation' + segmentationNo + '/sample_maxsegment.pdf'
    sam2fig.savefig(sam2figPath)
    file = open(dirPath + '/specfile.dat')
    content = file.readlines()
    overlap = content[1]
    fig3, ax3 = plt.subplots()
    ax3.set_aspect('equal')
    ax3.set_xlim(x1,x2)
    ax3.set_ylim(y1,y2)
    samPath_df.boundary.plot(ax=ax3, aspect=1, edgecolor='red', linewidth=1, zorder=2)
    samPath_df = samPath_df_org.iloc[[samIndexNo]] 
    samPath_df.boundary.plot(ax=ax, aspect=1, edgecolor='red', linewidth=1, zorder=2)
    for i in range(intersectNo):
        intersectarea = sample_segments['intersectarea'].iloc[i]
        segno = sample_segments['segmentno'].iloc[i]
        seg_area = sample_segments['segarea'].iloc[i]
        if intersectarea > float(overlap)*seg_area:
            segPath_df_temp = segPath_df.iloc[[segno-1]]
            segPath_df_temp.boundary.plot(ax=ax3, aspect=1, edgecolor='blue', linewidth=0.25)
    coor = samPath_df_org.iloc[[samIndexNo]].representative_point()
    plt.text(float(coor.geometry.x[samIndexNo]), float(coor.geometry.y[samIndexNo]), str(samIndexNo+1), color='red')
    plt.title("The sample with " + overlap + "overlap segments")
    samfig = ax3.get_figure()
    samfigPath = dirPath + '/segmentation' + segmentationNo + '/sample_overlapsegments.pdf'
    samfig.savefig(samfigPath)    
    messagebox.showinfo("Plot", "Sample and segments have been plotted and saved.")    
def calculateIndex(dirPath,k):
    fsname = dirPath + '/segmentation' + str(k) + '/result_Seg' + str(k) + '.dat'
    fs = open(fsname,"w")
    intPath = dirPath + '/segmentation' + str(k) + '/intersect.pkl'
    intersection_df  = pd.read_pickle(intPath)
    interLen = len(intersection_df)
    samplenoColumn = intersection_df["sampleno"]
    samLen = int(samplenoColumn.max())   
    def calculateAFI():
        tum_AFI = pd.DataFrame(columns = ['sampleno','segmentno','AFI'])
        overlap_AFI = pd.DataFrame(columns = ['sampleno','segmentno','AFI'])
        max_AFI = pd.DataFrame(columns = ['sampleno','segmentno','AFI'])        
        fs.write("--------------------------------------------------------\n")
        fs.write("-------------Area Fit Index (AFI)-----------------------\n")
        fs.write("AFI for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            AFI = (sam_area - seg_area)/ sam_area
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AFI = " + str(round(AFI, 3))+ "\n")
            new_tum_AFI_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'AFI': AFI}, index=[0])
            tum_AFI = pd.concat([tum_AFI, new_tum_AFI_row])
            top = top + AFI
        fs.write("\n")
        fs.write("AFI for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                AFI = (sam_area - seg_area)/ sam_area
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AFI = " + str(round(AFI, 3))+ "\n")
                new_over_AFI_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'AFI': AFI}, index=[0])
                overlap_AFI = pd.concat([overlap_AFI, new_over_AFI_row])
                top = top + AFI
                loopno = loopno+1
        fs.write("\n")
        fs.write("AFI for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            sam_area = select_samples['samparea'].iloc[selectMaxSample]
            seg_area = select_samples['segarea'].iloc[selectMaxSample]
            maxAFI = (sam_area - seg_area)/ sam_area
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  AFI = " + str(round(maxAFI, 3))+ "\n")
            new_max_AFI_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'AFI': maxAFI}, index=[0])
            max_AFI = pd.concat([max_AFI, new_max_AFI_row])
            top = top + maxAFI
        afiPath = dirPath + '/segmentation' + str(k) + '/AFI.pkl'
        overAFIPath = dirPath + '/segmentation' + str(k) + '/overlapAFI.pkl'
        maxafiPath = dirPath + '/segmentation' + str(k) +  '/maxAFI.pkl'
        tum_AFI.to_pickle(afiPath)
        overlap_AFI.to_pickle(overAFIPath)
        max_AFI.to_pickle(maxafiPath)
        afiPath_csv = dirPath + '/segmentation' + str(k) + '/AFI.csv'
        overlapAFIPath_csv = dirPath + '/segmentation' + str(k) + '/overlapAFI.csv'
        maxafiPath_csv = dirPath + '/segmentation' + str(k) +  '/maxAFI.csv'
        tum_AFI.to_csv(afiPath_csv, index=False)
        overlap_AFI.to_csv(overlapAFIPath_csv, index=False)
        max_AFI.to_csv(maxafiPath_csv, index=False)        
    def calculateMatch():
        tum_Match = pd.DataFrame(columns = ['sampleno','segmentno','Match'])
        overlap_Match = pd.DataFrame(columns = ['sampleno','segmentno','Match'])
        max_Match = pd.DataFrame(columns = ['sampleno','segmentno','Match'])
        fs.write("--------------------------------------------------------\n")
        fs.write("--------------------Match (M)---------------------------\n")
        fs.write("M for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            Match  = 1-(((intersectarea)**2/(seg_area*sam_area))**0.5)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  M = " + str(round(Match, 3))+ "\n")
            new_tum_Match_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'Match': Match}, index=[0])
            tum_Match = pd.concat([tum_Match, new_tum_Match_row])
            top = top + Match   
        fs.write("\n")
        fs.write("M for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                Match  = 1-(((intersectarea)**2/(seg_area*sam_area))**0.5)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  M = " + str(round(Match, 3))+ "\n")
                new_over_Match_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'Match': Match}, index=[0])
                overlap_Match = pd.concat([overlap_Match, new_over_Match_row])
                top = top + Match
                loopno = loopno+1                        
        fs.write("\n")
        fs.write("M for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            sam_area = select_samples['samparea'].iloc[selectMaxSample]
            seg_area = select_samples['segarea'].iloc[selectMaxSample]
            intersectarea = select_samples['intersectarea'].iloc[selectMaxSample]
            maxMatch = 1-(((intersectarea)**2/(seg_area*sam_area))**0.5)
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  M = " + str(round(maxMatch, 3))+ "\n")
            new_max_Match_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'Match': maxMatch}, index=[0])
            max_Match = pd.concat([max_Match, new_max_Match_row])
            top = top + maxMatch        
        matchPath = dirPath + '/segmentation' + str(k) + '/match.pkl'
        overlapmatchPath = dirPath + '/segmentation' + str(k) + '/overlapmatch.pkl'
        maxmatchPath = dirPath + '/segmentation' + str(k) + '/maxmatch.pkl'
        tum_Match.to_pickle(matchPath)
        overlap_Match.to_pickle(overlapmatchPath)
        max_Match.to_pickle(maxmatchPath)
        matchPath_csv = dirPath + '/segmentation' + str(k) + '/match.csv'
        overlapmatchPath_csv = dirPath + '/segmentation' + str(k) + '/overlapmatch.csv'
        maxmatchPath_csv = dirPath + '/segmentation' + str(k) +  '/maxmatch.csv'
        tum_Match.to_csv(matchPath_csv, index=False)
        overlap_Match.to_csv(overlapmatchPath_csv, index=False)
        max_Match.to_csv(maxmatchPath_csv, index=False)        
    def calculateQLoc():
        tum_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        overlap_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        max_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        fs.write("--------------------------------------------------------\n")
        fs.write("------------------QLoc (QL)-----------------------------\n")
        fs.write("QL for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  QL = " + str(round(qloc, 3))+ "\n")
            new_tum_qloc_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'qloc': qloc}, index=[0])
            tum_qloc = pd.concat([tum_qloc, new_tum_qloc_row])
            top = top + qloc       
        fs.write("\n")
        fs.write("QL for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  QL = " + str(round(qloc, 3))+ "\n")
                new_overlap_qloc_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'qloc': qloc}, index=[0])
                overlap_qloc = pd.concat([overlap_qloc, new_overlap_qloc_row])
                top = top + qloc
                loopno = loopno+1       
        fs.write("\n")
        fs.write("QL for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            maxqloc  = select_samples['distance'].iloc[selectMaxSample]
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  QL = " + str(round(maxqloc, 3))+ "\n")
            new_max_qloc_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'qloc': maxqloc}, index=[0])
            max_qloc = pd.concat([max_qloc, new_max_qloc_row])
            top = top + maxqloc      
        qlocPath = dirPath + '/segmentation' + str(k) + '/ql.pkl'
        overlapqlocPath = dirPath + '/segmentation' + str(k) + '/overlapql.pkl'
        maxqlocPath = dirPath + '/segmentation' + str(k) + '/maxql.pkl'
        tum_qloc.to_pickle(qlocPath)
        overlap_qloc.to_pickle(overlapqlocPath)
        max_qloc.to_pickle(maxqlocPath)
        qlocPath_csv = dirPath + '/segmentation' + str(k) + '/ql.csv'
        overlapqlocPath_csv = dirPath + '/segmentation' + str(k) + '/overlapql.csv'
        maxqlocPath_csv = dirPath + '/segmentation' + str(k) +  '/maxql.csv'
        tum_qloc.to_csv(qlocPath_csv, index=False)
        overlap_qloc.to_csv(overlapqlocPath_csv, index=False)
        max_qloc.to_csv(maxqlocPath_csv, index=False)        
    def calculateNormQLoc():
        tum_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        overlap_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        max_qloc = pd.DataFrame(columns = ['sampleno','segmentno','qloc'])
        tum_normQloc = pd.DataFrame(columns = ['sampleno','segmentno','normQloc'])
        overlap_normQloc = pd.DataFrame(columns = ['sampleno','segmentno','normQloc'])
        max_normQloc = pd.DataFrame(columns = ['sampleno','segmentno','normQloc'])        
        fs.write("--------------------------------------------------------\n")
        fs.write("-------------Relative Position (RP)---------------------\n")
        fs.write("RP for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            new_tum_qloc_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'qloc': qloc}, index=[0])
            tum_qloc = pd.concat([tum_qloc, new_tum_qloc_row])
        selectMaxDistance = tum_qloc['qloc'].max()
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            normQloc = qloc/selectMaxDistance
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  RP = " + str(round(normQloc, 3))+ "\n")
            new_tum_normQloc_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'normQloc': normQloc}, index=[0])
            tum_normQloc = pd.concat([tum_normQloc, new_tum_normQloc_row])
            top = top + normQloc
        fs.write("\n")
        fs.write("RP for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                new_overlap_qloc_row = pd.DataFrame({'sampleno': int(sampno), \
                                                     'segmentno': int(segno), \
                                  'qloc': qloc}, index=[0])
                overlap_qloc = pd.concat([overlap_qloc, new_overlap_qloc_row])
            selectMaxDistance = overlap_qloc['qloc'].max()
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            qloc  = intersection_df['distance'].iloc[i]
            normQloc = qloc/selectMaxDistance
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  RP = " + str(round(normQloc, 3))+ "\n")
                new_overlap_normQloc_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'RP': normQloc}, index=[0])
                overlap_normQloc = pd.concat([overlap_normQloc, new_overlap_normQloc_row])
                top = top + normQloc
                loopno = loopno+1                         
        fs.write("\n")
        fs.write("RP for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            maxqloc  = select_samples['distance'].iloc[selectMaxSample]
            new_max_qloc_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'qloc': maxqloc}, index=[0])
            max_qloc = pd.concat([max_qloc, new_max_qloc_row])
        selectMaxDistance = max_qloc['qloc'].max()
        for i in range(samLen):
            sampno = max_qloc['sampleno'].iloc[i]
            segno = max_qloc['segmentno'].iloc[i]
            qloc  = max_qloc['qloc'].iloc[i]
            normQloc = qloc/selectMaxDistance
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  RP = " + str(round(normQloc, 3))+ "\n")
            new_max_normQloc_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'normQloc': normQloc}, index=[0])
            max_normQloc = pd.concat([max_normQloc, new_max_normQloc_row])
            top = top + normQloc        
        normqlocPath = dirPath + '/segmentation' + str(k) + '/rp.pkl'
        overlapnormqlocPath = dirPath + '/segmentation' + str(k) + '/overlaprp.pkl'
        maxnormqlocPath = dirPath + '/segmentation' + str(k) + '/maxrp.pkl'
        tum_normQloc.to_pickle(normqlocPath)
        overlap_normQloc.to_pickle(overlapnormqlocPath)
        max_normQloc.to_pickle(maxnormqlocPath)
        normqlocPath_csv = dirPath + '/segmentation' + str(k) + '/rp.csv'
        overlapnormqlocPath_csv = dirPath + '/segmentation' + str(k) + '/overlaprp.csv'
        maxnormqlocPath_csv = dirPath + '/segmentation' + str(k) +  '/maxrp.csv'
        tum_normQloc.to_csv(normqlocPath_csv, index=False)
        overlap_normQloc.to_csv(overlapnormqlocPath_csv, index=False)
        max_normQloc.to_csv(maxnormqlocPath_csv, index=False)
    def calculateUnderSeg():
        tum_US = pd.DataFrame(columns = ['sampleno','segmentno','US'])
        overlap_US = pd.DataFrame(columns = ['sampleno','segmentno','US'])
        max_US = pd.DataFrame(columns = ['sampleno','segmentno','US'])
        fs.write("--------------------------------------------------------\n")
        fs.write("----------------Under Segmentation (US)-----------------\n")
        fs.write("US for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            US  = 1-(intersectarea/seg_area)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  US = " + str(round(US, 3))+ "\n")
            new_tum_US_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'US': US}, index=[0])
            tum_US = pd.concat([tum_US, new_tum_US_row])
            top = top + US        
        fs.write("\n")
        fs.write("US for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                US  = 1-(intersectarea/seg_area)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  US = " + str(round(US, 3))+ "\n")
                new_over_US_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'US': US}, index=[0])
                overlap_US = pd.concat([overlap_US, new_over_US_row])
                top = top + US
                loopno = loopno+1                
        fs.write("\n")
        fs.write("US for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            seg_area = select_samples['segarea'].iloc[selectMaxSample]
            intersectarea = select_samples['intersectarea'].iloc[selectMaxSample]
            maxUS = 1-(intersectarea/seg_area)
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  US = " + str(round(maxUS, 3))+ "\n")
            new_max_US_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'US': maxUS}, index=[0])
            max_US = pd.concat([max_US, new_max_US_row])
            top = top + maxUS       
        usPath = dirPath + '/segmentation' + str(k) + '/us.pkl'
        overlapusPath = dirPath + '/segmentation' + str(k) + '/oerlapus.pkl'
        maxusPath = dirPath + '/segmentation' + str(k) + '/maxus.pkl'
        tum_US.to_pickle(usPath)
        overlap_US.to_pickle(overlapusPath)
        max_US.to_pickle(maxusPath)
        usPath_csv = dirPath + '/segmentation' + str(k) + '/us.csv'
        overlapusPath_csv = dirPath + '/segmentation' + str(k) + '/overlapus.csv'
        maxusPath_csv = dirPath + '/segmentation' + str(k) +  '/maxus.csv'
        tum_US.to_csv(usPath_csv, index=False)
        overlap_US.to_csv(overlapusPath_csv, index=False)
        max_US.to_csv(maxusPath_csv, index=False)
    def calculateOverSeg():
        tum_OS = pd.DataFrame(columns = ['sampleno','segmentno','OS'])
        overlap_OS = pd.DataFrame(columns = ['sampleno','segmentno','OS'])
        max_OS = pd.DataFrame(columns = ['sampleno','segmentno','OS'])
        fs.write("--------------------------------------------------------\n")
        fs.write("----------------Over Segmentation (OS)------------------\n")
        fs.write("OS for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            OS  = 1-(intersectarea/sam_area)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  OS = " + str(round(OS, 3))+ "\n")
            new_tum_OS_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'OS': OS}, index=[0])
            tum_OS = pd.concat([tum_OS, new_tum_OS_row])
            top = top + OS        
        fs.write("\n")
        fs.write("OS for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            if intersectarea > olap*seg_area:
                OS  = 1-(intersectarea/sam_area)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  OS = " + str(round(OS, 3))+ "\n")
                new_over_OS_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'OS': OS}, index=[0])
                overlap_OS = pd.concat([overlap_OS, new_over_OS_row])
                top = top + OS
                loopno = loopno+1               
        fs.write("\n")
        fs.write("OS for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            sam_area = select_samples['samparea'].iloc[selectMaxSample]
            intersectarea = select_samples['intersectarea'].iloc[selectMaxSample]
            maxOS = 1-(intersectarea/sam_area)
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  OS = " + str(round(maxOS, 3))+ "\n")
            new_max_OS_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'OS': maxOS}, index=[0])
            max_OS = pd.concat([max_OS, new_max_OS_row])
            top = top + maxOS       
        osPath = dirPath + '/segmentation' + str(k) + '/os.pkl'
        overlaposPath = dirPath + '/segmentation' + str(k) + '/overlapos.pkl'
        maxosPath = dirPath + '/segmentation' + str(k) + '/maxos.pkl'
        tum_OS.to_pickle(osPath)
        overlap_OS.to_pickle(overlaposPath)
        max_OS.to_pickle(maxosPath)
        osPath_csv = dirPath + '/segmentation' + str(k) + '/os.csv'
        overlaposPath_csv = dirPath + '/segmentation' + str(k) + '/overplapos.csv'
        maxosPath_csv = dirPath + '/segmentation' + str(k) +  '/maxos.csv'
        tum_OS.to_csv(osPath_csv, index=False)
        overlap_OS.to_csv(overlaposPath_csv, index=False)
        max_OS.to_csv(maxosPath_csv, index=False)        
    def calculateOverSegUnderSeg():
        tum_OSUS = pd.DataFrame(columns = ['sampleno','segmentno','OSUS'])
        overlap_OSUS = pd.DataFrame(columns = ['sampleno','segmentno','OSUS'])
        max_OSUS = pd.DataFrame(columns = ['sampleno','segmentno','OSUS'])
        fs.write("--------------------------------------------------------\n")
        fs.write("------------Over & Under Segmentation (OUS)-------------\n")
        fs.write("OUS for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            OSUS  = math.sqrt((math.pow((1-(intersectarea/sam_area)),2) + math.pow((1-(intersectarea/seg_area)),2))/2)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  OUS = " + str(round(OSUS, 3))+ "\n")
            new_tum_OSUS_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'OSUS': OSUS}, index=[0])
            tum_OSUS = pd.concat([tum_OSUS, new_tum_OSUS_row])
            top = top + OSUS        
        fs.write("\n")
        fs.write("OUS for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            if intersectarea > olap*seg_area:
                OSUS  = math.sqrt((math.pow((1-(intersectarea/sam_area)),2) + math.pow((1-(intersectarea/seg_area)),2))/2)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  M = " + str(round(OSUS, 3))+ "\n")
                new_overlap_OSUS_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'OSUS': OSUS}, index=[0])
                overlap_OSUS = pd.concat([overlap_OSUS, new_overlap_OSUS_row])
                top = top + OSUS
                loopno = loopno+1          
        fs.write("\n")
        fs.write("OUS for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            sam_area = select_samples['samparea'].iloc[selectMaxSample]
            seg_area = select_samples['segarea'].iloc[selectMaxSample]
            intersectarea = select_samples['intersectarea'].iloc[selectMaxSample]
            maxOSUS = math.sqrt((math.pow((1-(intersectarea/sam_area)),2) + math.pow((1-(intersectarea/seg_area)),2))/2)
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  OUS = " + str(round(maxOSUS, 3))+ "\n")
            new_max_OSUS_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'OSUS': maxOSUS}, index=[0])
            max_OSUS = pd.concat([max_OSUS, new_max_OSUS_row])
            top = top + maxOSUS        
        osusPath = dirPath + '/segmentation' + str(k) + '/ous.pkl'
        overlaposusPath = dirPath + '/segmentation' + str(k) + '/overous.pkl'
        maxosusPath = dirPath + '/segmentation' + str(k) + '/maxous.pkl'
        tum_OSUS.to_pickle(osusPath)
        overlap_OSUS.to_pickle(overlaposusPath)
        max_OSUS.to_pickle(maxosusPath)
        osusPath_csv = dirPath + '/segmentation' + str(k) + '/ous.csv'
        overlaposusPath_csv = dirPath + '/segmentation' + str(k) + '/overlapous.csv'
        maxosusPath_csv = dirPath + '/segmentation' + str(k) +  '/maxous.csv'
        tum_OSUS.to_csv(osusPath_csv, index=False)
        overlap_OSUS.to_csv(overlaposusPath_csv, index=False)
        max_OSUS.to_csv(maxosusPath_csv, index=False)
    def calculateQualityRate():
        tum_QR = pd.DataFrame(columns = ['sampleno','segmentno','QRate'])
        overlap_QR = pd.DataFrame(columns = ['sampleno','segmentno','QRate'])
        max_QR = pd.DataFrame(columns = ['sampleno','segmentno','QRate'])
        fs.write("--------------------------------------------------------\n")
        fs.write("-------------------Quality Rate (QR)--------------------\n")
        fs.write("QR for all intersected segments: \n")
        top = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            QR  = 1-(intersectarea/(seg_area+sam_area-intersectarea))
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  QR = " + str(round(QR, 3))+ "\n")
            new_tum_QR_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'QRate': QR}, index=[0])
            tum_QR = pd.concat([tum_QR, new_tum_QR_row])
            top = top + QR        
        fs.write("\n")
        fs.write("QR for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            sam_area = intersection_df['samparea'].iloc[i]
            if intersectarea > olap*seg_area:
                QR  = 1-(intersectarea/(seg_area+sam_area-intersectarea))
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  QR = " + str(round(QR, 3))+ "\n")
                new_overlap_QR_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'QRate': QR}, index=[0])
                overlap_QR = pd.concat([overlap_QR, new_overlap_QR_row])
                top = top + QR
                loopno = loopno+1            
        fs.write("\n")
        fs.write("QR for maximum intersected segments: \n")
        top = 0
        for i in range(samLen):  
            select_samples = intersection_df.loc[intersection_df['sampleno'] == i+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            sam_area = select_samples['samparea'].iloc[selectMaxSample]
            seg_area = select_samples['segarea'].iloc[selectMaxSample]
            intersectarea = select_samples['intersectarea'].iloc[selectMaxSample]
            maxQR  = 1-(intersectarea/(seg_area+sam_area-intersectarea))
            fs.write("Sample no: " + str(i+1) + " segment no: " + str(int(segno)) +  "  QR = " + str(round(maxQR, 3))+ "\n")
            new_max_QR_row = pd.DataFrame({'sampleno': i+1, \
                              'segmentno': int(segno), \
                                  'QRate': maxQR}, index=[0])
            max_QR = pd.concat([max_QR, new_max_QR_row])
            top = top + maxQR       
        qrPath = dirPath + '/segmentation' + str(k) + '/qr.pkl'
        maxqrPath = dirPath + '/segmentation' + str(k) + '/maxqr.pkl'
        tum_QR.to_pickle(qrPath)
        max_QR.to_pickle(maxqrPath)
        qrPath_csv = dirPath + '/segmentation' + str(k) + '/qr.csv'
        maxqrPath_csv = dirPath + '/segmentation' + str(k) +  '/maxqr.csv'
        tum_QR.to_csv(qrPath_csv, index=False)
        max_QR.to_csv(maxqrPath_csv, index=False)
    def calculateOsusGlobal():
        tum_glOSUS = pd.DataFrame(columns = ['sampleno','segmentno','glosus'])
        overlap_glOSUS = pd.DataFrame(columns = ['sampleno','segmentno','glosus'])
        max_glOSUS = pd.DataFrame(columns = ['sampleno','segmentno','glosus'])
        fs.write("--------------------------------------------------------\n")
        fs.write("----------Accuracy Index (AI) based on OUS--------------\n")
        fs.write("Weight: " + str(w_coff)+ "\n")
        fs.write("AI-OUS for all intersected segments:\n")
        top = 0
        for i in range(normqlocLen):
            sampno = normqlocPath_df['sampleno'].iloc[i]
            segno = normqlocPath_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            osusValue = osusPath_df['OSUS'].iloc[i]
            globalAccValue = osusValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-OUS = " + str(round(globalAccValue, 3))+ "\n")
            new_tum_glOSUS_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glosus': globalAccValue}, index=[0])
            tum_glOSUS = pd.concat([tum_glOSUS, new_tum_glOSUS_row])
            top = top + globalAccValue        
        fs.write("\n")
        fs.write("AI-OUS for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            osusValue = osusPath_df['OSUS'].iloc[i]            
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                globalAccValue = osusValue*w_coff + qlocValue*(1-w_coff)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-OUS = " + str(round(globalAccValue, 3))+ "\n")
                new_overlap_glOSUS_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'glosus': globalAccValue}, index=[0])
                overlap_glOSUS = pd.concat([overlap_glOSUS, new_overlap_glOSUS_row])
                top = top + globalAccValue
                loopno = loopno+1                 
        fs.write("\n")
        fs.write("AI-OUS for maximum intersected segments:\n")
        top = 0              
        for i in range(maxnormqlocLen):
            sampno = maxnormqlocPath_df['sampleno'].iloc[i]
            segno = maxnormqlocPath_df['segmentno'].iloc[i]
            qlocValue = maxnormqlocPath_df['normQloc'].iloc[i]
            osusValue = maxosusPath_df['OSUS'].iloc[i]
            globalAccValue = osusValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-OUS = " + str(round(globalAccValue, 3))+ "\n")
            new_max_glOSUS_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glosus': globalAccValue}, index=[0])
            max_glOSUS = pd.concat([max_glOSUS, new_max_glOSUS_row])
            top = top + globalAccValue
        
        osusnqlocPath = dirPath + '/segmentation' + str(k) + '/ai_ous.pkl'
        overlaposusnqlocPath = dirPath + '/segmentation' + str(k) + '/overlap_ai_ous.pkl'
        maxosusnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_ous.pkl'
        tum_glOSUS.to_pickle(osusnqlocPath)
        overlap_glOSUS.to_pickle(overlaposusnqlocPath)
        max_glOSUS.to_pickle(maxosusnqlocPath)
        osusnqlocPath_csv = dirPath + '/segmentation' + str(k) + '/ai_ous.csv'
        overlaposusnqlocPath_csv = dirPath + '/segmentation' + str(k) + '/overlap_ai_ous.csv'
        maxosusnqloc_csv = dirPath + '/segmentation' + str(k) +  '/max_ai_ous.csv'
        tum_glOSUS.to_csv(osusnqlocPath_csv, index=False)
        overlap_glOSUS.to_csv(overlaposusnqlocPath_csv, index=False)
        max_glOSUS.to_csv(maxosusnqloc_csv, index=False)
    def calculateMatchGlobal():
        tum_glMatch = pd.DataFrame(columns = ['sampleno','segmentno','glmatch'])
        overlap_glMatch = pd.DataFrame(columns = ['sampleno','segmentno','glmatch'])
        max_glMatch = pd.DataFrame(columns = ['sampleno','segmentno','glmatch'])
        fs.write("--------------------------------------------------------\n")
        fs.write("----------Accuracy Index (AI) based on M----------------\n")
        fs.write("Weight: " + str(w_coff)+ "\n")
        fs.write("AI-M for all intersected segments: \n")
        top = 0
        for i in range(normqlocLen):
            sampno = normqlocPath_df['sampleno'].iloc[i]
            segno = normqlocPath_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            matchValue = matchPath_df['Match'].iloc[i]
            globalAccValue = matchValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-M = " + str(round(globalAccValue, 3))+ "\n")
            new_tum_glMatch_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glmatch': globalAccValue}, index=[0])
            tum_glMatch = pd.concat([tum_glMatch, new_tum_glMatch_row])
            top = top + globalAccValue
        fs.write("\n")
        fs.write("AI-M for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            matchValue = matchPath_df['Match'].iloc[i]            
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                globalAccValue = matchValue*w_coff + qlocValue*(1-w_coff)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-M = " + str(round(globalAccValue, 3))+ "\n")
                new_overlap_glMatch_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'glmatch': globalAccValue}, index=[0])
                overlap_glMatch = pd.concat([overlap_glMatch, new_overlap_glMatch_row])
                top = top + globalAccValue
                loopno = loopno+1           
        fs.write("\n")
        fs.write("AI-M for maximum intersected segments: \n")
        top = 0               
        for i in range(maxnormqlocLen):
            sampno = maxnormqlocPath_df['sampleno'].iloc[i]
            segno = maxnormqlocPath_df['segmentno'].iloc[i]
            qlocValue = maxnormqlocPath_df['normQloc'].iloc[i]
            matchValue = maxmatchPath_df['Match'].iloc[i]
            globalAccValue = matchValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-M = " + str(round(globalAccValue, 3))+ "\n")
            new_max_glMatch_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glmatch': globalAccValue}, index=[0])
            max_glMatch = pd.concat([max_glMatch, new_max_glMatch_row])
            top = top + globalAccValue
        matchnqlocPath = dirPath + '/segmentation' + str(k) + '/ai_m.pkl'
        overlapmatchnqlocPath = dirPath + '/segmentation' + str(k) + '/overlap_ai_m.pkl'
        maxmatchnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_m.pkl'
        tum_glMatch.to_pickle(matchnqlocPath)
        overlap_glMatch.to_pickle(overlapmatchnqlocPath)
        max_glMatch.to_pickle(maxmatchnqlocPath)
        matchnqlocPath_csv = dirPath + '/segmentation' + str(k) + '/ai_m.csv'
        overlapmatchnqlocPath_csv = dirPath + '/segmentation' + str(k) + '/overlap_ai_m.csv'
        maxmatchnqloc_csv = dirPath + '/segmentation' + str(k) +  '/max_ai_m.csv'
        tum_glMatch.to_csv(matchnqlocPath_csv, index=False)
        overlap_glMatch.to_csv(overlapmatchnqlocPath_csv, index=False)
        max_glMatch.to_csv(maxmatchnqloc_csv, index=False)        
    def calculateQRGlobal():
        tum_glQR = pd.DataFrame(columns = ['sampleno','segmentno','glqr'])
        overlap_glQR = pd.DataFrame(columns = ['sampleno','segmentno','glqr'])
        max_glQR = pd.DataFrame(columns = ['sampleno','segmentno','glqr'])
        fs.write("--------------------------------------------------------\n")
        fs.write("-----------Accuracy Index (AI) based on QR--------------\n")
        fs.write("Weight: " + str(w_coff)+ "\n")
        fs.write("AI-QR for all intersected segments: \n")
        top = 0
        for i in range(normqlocLen):
            sampno = normqlocPath_df['sampleno'].iloc[i]
            segno = normqlocPath_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            qrValue = qrPath_df['QRate'].iloc[i]
            globalAccValue = qrValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-QR = " + str(round(globalAccValue, 3))+ "\n")
            new_tum_glQR_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glqr': globalAccValue}, index=[0])
            tum_glQR = pd.concat([tum_glQR, new_tum_glQR_row])
            top = top + globalAccValue                
        fs.write("\n")
        fs.write("AI-QR for minimum " + str(olap) + " overlap between the segments and sample: \n")
        top = 0
        loopno = 0
        for i in range(interLen):
            sampno = intersection_df['sampleno'].iloc[i]
            segno = intersection_df['segmentno'].iloc[i]
            qlocValue = normqlocPath_df['normQloc'].iloc[i]
            qrValue = qrPath_df['QRate'].iloc[i]           
            intersectarea = intersection_df['intersectarea'].iloc[i]
            seg_area = intersection_df['segarea'].iloc[i]
            if intersectarea > olap*seg_area:
                globalAccValue = qrValue*w_coff + qlocValue*(1-w_coff)
                fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-QR = " + str(round(globalAccValue, 3))+ "\n")
                new_overlap_glQR_row = pd.DataFrame({'sampleno': int(sampno), \
                                                'segmentno': int(segno), \
                                                    'glqr': globalAccValue}, index=[0])
                overlap_glQR = pd.concat([overlap_glQR, new_overlap_glQR_row])
                top = top + globalAccValue
                loopno = loopno+1         
        fs.write("\n")
        fs.write("AI-QR for maximum intersected segments: \n")
        top = 0              
        for i in range(maxnormqlocLen):
            sampno = maxnormqlocPath_df['sampleno'].iloc[i]
            segno = maxnormqlocPath_df['segmentno'].iloc[i]
            qlocValue = maxnormqlocPath_df['normQloc'].iloc[i]
            qrValue = maxqrPath_df['QRate'].iloc[i]
            globalAccValue = qrValue*w_coff + qlocValue*(1-w_coff)
            fs.write("Sample no: " + str(int(sampno)) + " segment no: " + str(int(segno)) +  "  AI-QR = " + str(round(globalAccValue, 3))+ "\n")
            new_max_glQR_row = pd.DataFrame({'sampleno': int(sampno), \
                              'segmentno': int(segno), \
                                  'glqr': globalAccValue}, index=[0])
            max_glQR = pd.concat([max_glQR, new_max_glQR_row])
            top = top + globalAccValue       
        qrnqlocPath = dirPath + '/segmentation' + str(k) + '/ai_qr.pkl'
        maxqrnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_qr.pkl'
        tum_glQR.to_pickle(qrnqlocPath)
        max_glQR.to_pickle(maxqrnqlocPath)
        qrnqlocPath_csv = dirPath + '/segmentation' + str(k) + '/ai_qr.csv'
        maxqrnqloc_csv = dirPath + '/segmentation' + str(k) +  '/max_ai_qr.csv'
        tum_glQR.to_csv(qrnqlocPath_csv, index=False)
        max_glQR.to_csv(maxqrnqloc_csv, index=False)        
    olap = float(e42.get()) 
    if afi_var.get() == 1:
        calculateAFI()
    if match_var.get() == 1:
        calculateMatch()
    if dist_var.get() == 1:
        calculateQLoc()
    if norm_dist_var.get() == 1:
        calculateNormQLoc()
    if us_var.get() == 1:
        calculateUnderSeg()
    if os_var.get() == 1:
        calculateOverSeg()
    if qr_var.get() == 1:
        calculateQualityRate()
    if osus_var.get() == 1:
        calculateOverSegUnderSeg()
    w_coff = float(e30.get())    
    specFile = dirPath + '/specfile.dat'
    sf = open(specFile,"w")
    sf.write("Minimum overlap for sample objects:\n")
    sf.write(str(olap)+"\n") 
    sf.write("Weight_area:\n")
    sf.write(str(w_coff)+"\n")
    sf.write("Directory Path:\n")
    sf.write(str(dirPath)+"\n")
    sf.write("Segmentation no:\n")
    sf.write(str(segmentationNum2.get()))    
    sf.close()   
    if osus_var.get() == 1 and norm_dist_var.get() == 1:
        normqlocPath = dirPath + '/segmentation' + str(k) + '/rp.pkl'
        normqlocPath_df  = pd.read_pickle(normqlocPath)
        normqlocLen = len(normqlocPath_df)
        osusPath = dirPath + '/segmentation' + str(k) + '/ous.pkl'
        osusPath_df  = pd.read_pickle(osusPath)
        maxnormqlocPath = dirPath + '/segmentation' + str(k) + '/maxrp.pkl'
        maxnormqlocPath_df  = pd.read_pickle(maxnormqlocPath)
        maxnormqlocLen = len(maxnormqlocPath_df)
        maxosusPath = dirPath + '/segmentation' + str(k) + '/maxous.pkl'
        maxosusPath_df  = pd.read_pickle(maxosusPath)
        calculateOsusGlobal()        
    if match_var.get() == 1 and norm_dist_var.get() == 1:
        normqlocPath = dirPath + '/segmentation' + str(k) + '/rp.pkl'
        normqlocPath_df  = pd.read_pickle(normqlocPath)
        normqlocLen = len(normqlocPath_df)
        matchPath = dirPath + '/segmentation' + str(k) + '/match.pkl'
        matchPath_df  = pd.read_pickle(matchPath)        
        maxnormqlocPath = dirPath + '/segmentation' + str(k) + '/maxrp.pkl'
        maxnormqlocPath_df  = pd.read_pickle(maxnormqlocPath)
        maxnormqlocLen = len(maxnormqlocPath_df)
        maxmatchPath = dirPath + '/segmentation' + str(k) + '/maxmatch.pkl'
        maxmatchPath_df  = pd.read_pickle(maxmatchPath)
        calculateMatchGlobal()        
    if qr_var.get() == 1 and norm_dist_var.get() == 1:
        normqlocPath = dirPath + '/segmentation' + str(k) + '/rp.pkl'
        normqlocPath_df  = pd.read_pickle(normqlocPath)
        normqlocLen = len(normqlocPath_df)
        qrPath = dirPath + '/segmentation' + str(k) + '/qr.pkl'
        qrPath_df  = pd.read_pickle(qrPath)       
        maxnormqlocPath = dirPath + '/segmentation' + str(k) + '/maxrp.pkl'
        maxnormqlocPath_df  = pd.read_pickle(maxnormqlocPath)
        maxnormqlocLen = len(maxnormqlocPath_df)
        maxqrPath = dirPath + '/segmentation' + str(k) + '/maxqr.pkl'
        maxqrPath_df  = pd.read_pickle(maxqrPath)  
        calculateQRGlobal()
    if qr_var.get() == 1  and match_var.get() == 1 and osus_var.get() == 1 and norm_dist_var.get() == 1:
        maxnormqlocPath = dirPath + '/segmentation' + str(k) + '/maxrp.pkl'
        maxnormqlocPath_df  = pd.read_pickle(maxnormqlocPath)
        maxnormqlocLen = len(maxnormqlocPath_df)
        maxnormloc_df = maxnormqlocPath_df[['normQloc']].copy()
        maxqrPath = dirPath + '/segmentation' + str(k) + '/maxqr.pkl'
        maxqrPath_df  = pd.read_pickle(maxqrPath)
        maxQRate_df = maxqrPath_df[['QRate']].copy()        
        maxmatchPath = dirPath + '/segmentation' + str(k) + '/maxmatch.pkl'
        maxmatchPath_df  = pd.read_pickle(maxmatchPath)
        maxMatch_df = maxmatchPath_df[['Match']].copy()
        maxosusPath = dirPath + '/segmentation' + str(k) + '/maxous.pkl'
        maxosusPath_df  = pd.read_pickle(maxosusPath)
        maxOSUS_df = maxosusPath_df[['OSUS']].copy()        
        maxnormloc_df.reset_index(drop=True, inplace=True)
        maxQRate_df.reset_index(drop=True, inplace=True)
        maxMatch_df.reset_index(drop=True, inplace=True)
        maxOSUS_df.reset_index(drop=True, inplace=True)        
        maxloc_QR_M_OSUS_df = pd.concat([maxnormloc_df, maxQRate_df, maxMatch_df, maxOSUS_df], axis=1)
        ax = maxloc_QR_M_OSUS_df.plot.scatter(x="normQloc", y="QRate", s=3, color="DarkBlue", label="QR", zorder=3)
        maxloc_QR_M_OSUS_df.plot.scatter(x="normQloc", y="Match", s=3, color="DarkGreen", label="M", zorder=3, ax=ax);
        maxloc_QR_M_OSUS_df.plot.scatter(x="normQloc", y="OSUS", s=3, color="Red", label="OUS", zorder=3, ax=ax);
        ax.grid('on', axis='x')
        ax.grid('on', axis='y')
        ax.grid(zorder=0)
        plt.xlim(0,1.025)
        plt.ylim(0,1.025)
        maxfigPath = dirPath + '/segmentation' + str(k) + '/criteria.pdf'
        ax.set_ylabel('Area-based criteria')
        ax.set_xlabel('Relative Position')
        maxfig = ax.get_figure()
        maxfig.savefig(maxfigPath)        
        maxqrnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_qr.pkl'
        maxqrnqlocPath_df  = pd.read_pickle(maxqrnqlocPath)
        maxQRatenqloc_df = maxqrnqlocPath_df[['sampleno','glqr']].copy()        
        maxmatchnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_m.pkl'
        maxmatchnqlocPath_df  = pd.read_pickle(maxmatchnqlocPath)
        maxMatchnqloc_df = maxmatchnqlocPath_df[['glmatch']].copy()
        maxosusnqlocPath = dirPath + '/segmentation' + str(k) + '/max_ai_ous.pkl'
        maxosusnqlocPath_df  = pd.read_pickle(maxosusnqlocPath)
        maxOSUSnqloc_df = maxosusnqlocPath_df[['glosus']].copy()        
        maxQRatenqloc_df.reset_index(drop=True, inplace=True)
        maxMatchnqloc_df.reset_index(drop=True, inplace=True)
        maxOSUSnqloc_df.reset_index(drop=True, inplace=True)        
        maxloc_QR_M_OSUS_Acc_df = pd.concat([maxQRatenqloc_df, maxMatchnqloc_df, maxOSUSnqloc_df], axis=1)
        ax = maxloc_QR_M_OSUS_Acc_df.plot.scatter(x="sampleno", y="glqr", s=3, color="DarkBlue", label="AI-QR", zorder=3)
        maxloc_QR_M_OSUS_Acc_df.plot.scatter(x="sampleno", y="glmatch", s=3, color="DarkGreen", label="AI-M", zorder=3, ax=ax);
        maxloc_QR_M_OSUS_Acc_df.plot.scatter(x="sampleno", y="glosus", s=3, color="Red", label="AI-OUS", zorder=3, ax=ax);
        plt.ylim(0,1.025)
        maxfigPath = dirPath + '/segmentation' + str(k) + '/indexes.pdf'
        ax.set_ylabel('Accuracy')
        ax.set_xlabel('Sample no')
        ax.grid('on', axis='x')
        ax.grid('on', axis='y')
        ax.grid(zorder=0)
        maxfig = ax.get_figure()
        maxfig.savefig(maxfigPath)       
    fs.write("\n")
    fs.write("End of file.")
    fs.close()    
def createPoly():
    dirPath = e3.get()
    file = open(dirPath + '/specfile.dat')
    content = file.readlines()
    k = content[7]
    olap=float(content[1])    
    for i in range(int(k)):
        fsname_int = dirPath + '/segmentation' + str(i+1) + '/intersect.pkl'
        pol_intersect = pd.read_pickle(fsname_int)
        fsname = dirPath + '/segmentation' + str(i+1) + '/segment.pkl'
        segment_gdf = pd.read_pickle(fsname)
        new_segments = segment_gdf
        new_segments = new_segments.head(0)
        for j in range(len(pol_intersect)):
            segno = pol_intersect['segmentno'].iloc[j]
            new_segments = pd.concat([new_segments, segment_gdf.iloc[[int(segno)-1]]])
        new_segments.to_file(dirPath + '/segmentation' + str(i+1) + '/all_labels.shp')    
    fsname_samp = dirPath + '/sample.pkl'
    pol_samp = pd.read_pickle(fsname_samp)    
    for i in range(int(k)):
        fsname_int = dirPath + '/segmentation' + str(i+1) + '/intersect.pkl'
        pol_intersect = pd.read_pickle(fsname_int)    
        fsname = dirPath + '/segmentation' + str(i+1) + '/segment.pkl'
        segment_gdf = pd.read_pickle(fsname)
        new_segments = segment_gdf
        new_segments = new_segments.head(0)
        for j in range(len(pol_samp)):
            select_samples = pol_intersect.loc[pol_intersect['sampleno'] == j+1]
            selectMaxSample = select_samples['intersectarea'].argmax()
            segno = select_samples['segmentno'].iloc[selectMaxSample]
            new_segments = pd.concat([new_segments, segment_gdf.iloc[[int(segno)-1]]])
        new_segments.to_file(dirPath + '/segmentation' + str(i+1) + '/max_labels.shp')        
    for i in range(int(k)):
        fsname_int = dirPath + '/segmentation' + str(i+1) + '/intersect.pkl'
        pol_intersect = pd.read_pickle(fsname_int)
        fsname = dirPath + '/segmentation' + str(i+1) + '/segment.pkl'
        segment_gdf = pd.read_pickle(fsname)
        new_segments = segment_gdf
        new_segments = new_segments.head(0)
        for j in range(len(pol_intersect)):
            segno = pol_intersect['segmentno'].iloc[j]
            intersectarea = pol_intersect['intersectarea'].iloc[j]
            seg_area = pol_intersect['segarea'].iloc[j]
            if intersectarea > olap*seg_area:
                new_segments = pd.concat([new_segments, segment_gdf.iloc[[int(segno)-1]]])
        new_segments.to_file(dirPath + '/segmentation' + str(i+1) + '/overlap_labels.shp')    
def showProject():
    messagebox.showinfo("PySAAT", "Segmentation Accuracy Analyst Toolbox Version 1.0 - 2023")    
def show_pdf():
    subprocess.Popen("InfoTable.pdf",shell=True)    
def loadSegFile():
    try:
        workPath = e3.get()
        segFileName = filedialog.askopenfilename(initialdir = workPath, title = "Select file",filetypes = (("shape files","*.shp"),("all files","*.*")))
        return segFileName
    except:
        messagebox.showerror("Error", "An error occured while selecting segmentation file.")        
def loadSamFile():
    try:
        workPath = e3.get()
        samFileName = filedialog.askopenfilename(initialdir = workPath, title = "Select file",filetypes = (("shape files","*.shp"),("all files","*.*")))
        e2.delete(0, 'end')
        e2.insert(100,samFileName)
    except:
        messagebox.showerror("Error", "An error occured while selecting object file.")
def browseDirectory():
    directoryPath = filedialog.askdirectory(initialdir = "/")
    e3.delete(0, 'end')
    e3.insert(100,directoryPath)
root = tk.Tk() 
root.title("PySAAT - Python-based Segmentation Accuracy Analysis Toolbox") 
root.geometry('840x700')
tabControl = ttk.Notebook(root) 
tab1 = ttk.Frame(tabControl) 
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)
tab4 = ttk.Frame(tabControl)
tabControl.add(tab1, text ='  Working Directory ') 
tabControl.add(tab2, text ='       Import       ')
tabControl.add(tab3, text ='       Process      ')
tabControl.add(tab4, text ='        Plot        ')  
tabControl.pack(expand = 1, fill ="both") 
#######
#tab1
#######
ttk.Separator(tab1, orient='horizontal').grid(row=1, columnspan=6, sticky="ew", pady=10, padx=10)
ttk.Label(tab1, text ="Working Directory", font="Helvetica 11 bold").grid(row=2, columnspan=6, sticky="s", padx=4, pady=4)
ttk.Label(tab1, text="Directory path:").grid(row=3, column=0, sticky="e", pady=4, padx=4)
e3 = ttk.Entry(tab1, width=85)
e3.grid(row=3, column=1, pady=4, padx=4)
ttk.Button(tab1, text='Browse', command=browseDirectory).grid(row=3, column=2, sticky="s", pady=4, padx=4)
ttk.Separator(tab1, orient='horizontal').grid(row=4, columnspan=6, sticky="ew", pady=10, padx=10)
#######
#tab2
#######
ttk.Separator(tab2, orient='horizontal').grid(row=0, columnspan=6, sticky="ew", pady=10, padx=10)
ttk.Label(tab2, text ="Choose an import source", font="Helvetica 11 bold").grid(row=1, columnspan=6, sticky="s", padx=4, pady=4)
source_var = tk.IntVar() #value=10
def selected():
     if source_var.get()==5:
         e2.state(['!disabled'])
         samBrowseBut.state(['!disabled'])
         fileImpLab.state(['!disabled'])
         numSegLab.state(['!disabled'])
         samLabel.state(['!disabled'])
         segmentationNum.state(['!disabled'])
         preProceBut.state(['!disabled'])
         progressLabel2.state(['!disabled'])
         progressLabel3.state(['!disabled'])
         my_progress.state(['!disabled'])
         overall_progress.state(['!disabled'])
         imDBLab.state(['disabled'])         
         dbnameBut.state(['disabled'])
         e10.state(['disabled'])
         usnameBut.state(['disabled'])
         e11.state(['disabled'])
         passBut.state(['disabled'])
         e12.state(['disabled'])
         hostBut.state(['disabled'])
         e13.state(['disabled'])
         portBut.state(['disabled'])
         e14.state(['disabled'])
         samtbBut.state(['disabled'])
         e15.state(['disabled'])         
         samgcnLab.state(['disabled'])
         e16.state(['disabled'])
         nsegtabLab.state(['disabled'])
         segmentationNum_db.state(['disabled'])
         preProceButDB.state(['disabled'])                  
     elif source_var.get()==10:
         e2.state(['disabled'])
         samBrowseBut.state(['disabled'])
         fileImpLab.state(['disabled'])
         numSegLab.state(['disabled'])
         samLabel.state(['disabled'])
         segmentationNum.state(['disabled'])
         preProceBut.state(['disabled'])
         progressLabel2.state(['!disabled'])
         progressLabel3.state(['!disabled'])
         my_progress.state(['!disabled'])
         overall_progress.state(['!disabled'])
         imDBLab.state(['!disabled'])         
         dbnameBut.state(['!disabled'])
         e10.state(['!disabled'])
         usnameBut.state(['!disabled'])
         e11.state(['!disabled'])
         passBut.state(['!disabled'])
         e12.state(['!disabled'])         
         hostBut.state(['!disabled'])
         e13.state(['!disabled'])
         portBut.state(['!disabled'])
         e14.state(['!disabled'])
         samtbBut.state(['!disabled'])
         e15.state(['!disabled'])         
         samgcnLab.state(['!disabled'])
         e16.state(['!disabled'])
         nsegtabLab.state(['!disabled'])
         segmentationNum_db.state(['!disabled'])
         preProceButDB.state(['!disabled'])
rb1 = ttk.Radiobutton(tab2, text='geospatial files', variable=source_var, value=5, command=selected)
rb2 = ttk.Radiobutton(tab2, text='geospatial databases', variable=source_var, value=10, command=selected)
rb1.grid(row=2, column=0, sticky="e", pady=4, padx=4)
rb2.grid(row=2, column=1, sticky="e", pady=4, padx=4)
ttk.Separator(tab2, orient='horizontal').grid(row=3, columnspan=6, sticky="ew", pady=10, padx=10)
fileImpLab = ttk.Label(tab2, text ="Import from Geospatial Files", font="Helvetica 11 bold")
fileImpLab.grid(row=4, columnspan=6, sticky="s", padx=4, pady=4)
samLabel = ttk.Label(tab2, text="Samples file (.shp) : ")
samLabel.grid(row=5, column=0, sticky="e", pady=4, padx=4)
e2 = ttk.Entry(tab2, width=85)
e2.grid(row=5, column=1, pady=4, padx=4)
samBrowseBut = ttk.Button(tab2, text='Browse', command=loadSamFile)
samBrowseBut.grid(row=5, column=2, sticky="s", pady=4, padx=4)
numSegLab = ttk.Label(tab2, text="Define number of segmentation files : ")
numSegLab.grid(row=6, column=0, sticky="e", pady=4, padx=4)
n = tk.StringVar() 
segmentationNum = ttk.Combobox(tab2,text='segmentationNum', width = 4, state="readonly", textvariable = n)
segmentationNum['values'] = ('1','2','3','4','5', '6', '7', '8', '9', '10') 
segmentationNum.grid(row=6, column=1, sticky="w", pady=4, padx=4) 
segmentationNum.current()
preProceBut = ttk.Button(tab2, text='Browse segmentation file(s) and start pre-process ...', command=runPreprocess, width = 70)
preProceBut.grid(row=7, column=1, sticky="w", pady=4, padx=4)
ttk.Separator(tab2, orient='horizontal').grid(row=8, columnspan=6, sticky="ew", pady=4, padx=10)
imDBLab = ttk.Label(tab2, text ="Import from Geospatial Database", font="Helvetica 11 bold")
imDBLab.grid(row=9, columnspan=6, sticky="s", padx=4, pady=4)
dbnameBut = ttk.Label(tab2, text="Database name : ")
dbnameBut.grid(row=10, column=0, sticky="e", pady=4, padx=4)
e10 = ttk.Entry(tab2, width=30)
e10.insert(0, "geospatial_db")
e10.grid(row=10, column=1, sticky="w", pady=4, padx=4)
usnameBut = ttk.Label(tab2, text="Username : ")
usnameBut.grid(row=11, column=0, sticky="e", pady=4, padx=4)
e11 = ttk.Entry(tab2, width=30)
e11.grid(row=11, column=1, sticky="w", pady=4, padx=4)
e11.insert(0, "postgres")
passBut = ttk.Label(tab2, text="Password : ")
passBut.grid(row=12, column=0, sticky="e", pady=4, padx=4)
e12 = ttk.Entry(tab2, width=30, show = "*")
e12.grid(row=12, column=1, sticky="w", pady=4, padx=4)
e12.insert(0, "123")
hostBut = ttk.Label(tab2, text="Host : ")
hostBut.grid(row=13, column=0, sticky="e", pady=4, padx=4)
e13 = ttk.Entry(tab2, width=30)
e13.grid(row=13, column=1, sticky="w", pady=4, padx=4)
e13.insert(0, "localhost")
portBut = ttk.Label(tab2, text="Port : ")
portBut.grid(row=14, column=0, sticky="e", pady=4, padx=4)
e14 = ttk.Entry(tab2, width=30)
e14.grid(row=14, column=1, sticky="w", pady=4, padx=4)
e14.insert(0, "5432")
samtbBut = ttk.Label(tab2, text="Sample table name : ")
samtbBut.grid(row=15, column=0, sticky="e", pady=4, padx=4)
e15 = ttk.Entry(tab2, width=30)
e15.grid(row=15, column=1, sticky="w", pady=4, padx=4)
e15.insert(0, "samples")
samgcnLab = ttk.Label(tab2, text="Sample geometry column name : ")
samgcnLab.grid(row=16, column=0, sticky="e", pady=4, padx=4)
e16 = ttk.Entry(tab2, width=30)
e16.grid(row=16, column=1, sticky="w", pady=4, padx=4)
e16.insert(0, "geom")
nsegtabLab = ttk.Label(tab2, text="Define number of segmentation tables : ")
nsegtabLab.grid(row=17, column=0, sticky="e", pady=4, padx=4)
n_db = tk.StringVar() 
segmentationNum_db = ttk.Combobox(tab2,text='segmentationNum', width = 4, state="readonly", textvariable = n_db)
segmentationNum_db['values'] = ('1','2','3','4','5', '6', '7', '8', '9', '10') 
segmentationNum_db.grid(row=17, column=1, sticky="w", pady=4, padx=4) 
segmentationNum_db.current()
preProceButDB = ttk.Button(tab2, text='Connect to the database and segmentation table(s) and start pre-process ...', command=runPreprocess_db, width = 70)
preProceButDB.grid(row=18, column=1, sticky="w", pady=4, padx=4)
ttk.Separator(tab2, orient='horizontal').grid(row=19, columnspan=6, sticky="ew", pady=4, padx=10)
barText = ""
progressLabel = ttk.Label(tab2, text=barText)
progressLabel.grid(row=20, column=1, sticky="w", pady=4, padx=4)
bar2Text = "Segmentation process : "
progressLabel2 = ttk.Label(tab2, text=bar2Text)
progressLabel2.grid(row=21, column=0, sticky="se", pady=4, padx=4)
my_progress = ttk.Progressbar(tab2, length=300, orient='horizontal', mode='determinate')
my_progress.grid(row=21, column=1, sticky="w", pady=4, padx=4)
barText4 = ""
progressLabel4 = ttk.Label(tab2, text=barText4)
progressLabel4.grid(row=21, column=2, sticky="sw", pady=4, padx=4)
bar3Text = "Overall process : "
progressLabel3 = ttk.Label(tab2, text=bar3Text)
progressLabel3.grid(row=22, column=0, sticky="se", pady=4, padx=4)
overall_progress = ttk.Progressbar(tab2, length=300, orient='horizontal', mode='determinate')
overall_progress.grid(row=22, column=1, sticky="w", pady=4, padx=4)
barText5 = ""
progressLabel5 = ttk.Label(tab2, text=barText5)
progressLabel5.grid(row=22, column=2, sticky="sw", pady=4, padx=4)
e2.state(['disabled'])
samBrowseBut.state(['disabled'])
fileImpLab.state(['disabled'])
numSegLab.state(['disabled'])
samLabel.state(['disabled'])
segmentationNum.state(['disabled'])
preProceBut.state(['disabled'])
imDBLab.state(['disabled'])         
dbnameBut.state(['disabled'])
e10.state(['disabled'])
usnameBut.state(['disabled'])
e11.state(['disabled'])
passBut.state(['disabled'])
e12.state(['disabled'])
hostBut.state(['disabled'])
e13.state(['disabled'])
portBut.state(['disabled'])
e14.state(['disabled'])
samtbBut.state(['disabled'])
e15.state(['disabled'])         
samgcnLab.state(['disabled'])
e16.state(['disabled'])
nsegtabLab.state(['disabled'])
segmentationNum_db.state(['disabled'])
preProceButDB.state(['disabled'])
progressLabel2.state(['disabled'])
progressLabel3.state(['disabled'])
my_progress.state(['disabled'])
overall_progress.state(['disabled'])
#######
#tab3
#######
ttk.Separator(tab3, orient='horizontal').grid(row=0, columnspan=6, sticky="ew", pady=4, padx=10)
nsegtabLab2 = ttk.Label(tab3, text="                       Define number of segmentation directories :      ")
nsegtabLab2.grid(row=1, column=0, sticky="e", pady=4, padx=4)
n2 = tk.StringVar() 
segmentationNum2 = ttk.Combobox(tab3,text='segmentationNum', width = 4, state="readonly", textvariable = n2)
segmentationNum2['values'] = ('1','2','3','4','5', '6', '7', '8', '9', '10') 
segmentationNum2.grid(row=1, column=1, sticky="w", pady=4, padx=4) 
segmentationNum2.current()
ttk.Separator(tab3, orient='horizontal').grid(row=2, columnspan=6, sticky="ew", pady=4, padx=10)

ttk.Label(tab3, text="Minimum overlap for sample objects:             ").grid(row=3, column=0, sticky="e", pady=4, padx=4)
e42 = ttk.Entry(tab3, width=5)
e42.grid(row=3, column=1, sticky="w", pady=4, padx=4)
e42.insert(0, "0.75")
ttk.Separator(tab3, orient='horizontal').grid(row=4, columnspan=6, sticky="ew", pady=4, padx=10)

ttk.Label(tab3, text ="Area-based criteria", font="Helvetica 11 bold").grid(row=5, columnspan=6, sticky="s", padx=4, pady=4)
afi_var = tk.IntVar(value=1)
match_var = tk.IntVar(value=1)
dist_var = tk.IntVar(value=1)
norm_dist_var = tk.IntVar(value=1)
us_var = tk.IntVar(value=1)
os_var = tk.IntVar(value=1)
qr_var = tk.IntVar(value=1)
osus_var = tk.IntVar(value=1)
ttk.Checkbutton(tab3, text="Area Fit Index (AFI)   ", variable=afi_var).grid(row=7, column=0, sticky="e", pady=4, padx=4)
ttk.Checkbutton(tab3, text="Match (M)              ", variable=match_var).grid(row=7, column=2, sticky="w", pady=4, padx=4)
ttk.Checkbutton(tab3, text="Under Segmentation (US) ", variable=us_var).grid(row=8, column=0, sticky="e",pady=4, padx=4)
ttk.Checkbutton(tab3, text="OverSegmentation (OS)  ", variable=os_var).grid(row=8, column=2, sticky="w", pady=4, padx=4)
ttk.Checkbutton(tab3, text="Under & Over Segmentation (OUS) ", variable=osus_var).grid(row=9, column=0, sticky="e",pady=4, padx=4)
ttk.Checkbutton(tab3, text="Quality Rate (QR)      ", variable=qr_var).grid(row=9, column=2, sticky="w", pady=4, padx=4)
ttk.Separator(tab3, orient='horizontal').grid(row=10, columnspan=6, sticky="ew", pady=4, padx=10)
ttk.Label(tab3, text ="Location-based criteria", font="Helvetica 11 bold").grid(row=11, columnspan=6, sticky="s", padx=4, pady=4)
ttk.Checkbutton(tab3, text="QLoc (QL)              ", variable=dist_var).grid(row=12, column=0, sticky="e", pady=4, padx=4)
ttk.Checkbutton(tab3, text="Relative Position (RP)              ", variable=norm_dist_var).grid(row=12, column=2, sticky="w", pady=4, padx=4)
ttk.Separator(tab3, orient='horizontal').grid(row=13, columnspan=6, sticky="ew", pady=4, padx=10)
ttk.Label(tab3, text ="Accuracy indexes", font="Helvetica 11 bold").grid(row=14, columnspan=6, sticky="s", padx=4, pady=4)
ttk.Label(tab3, text="Define a weight coefficient for the area-based criteria:     W_area = ").grid(row=15, column=0, sticky="e", pady=4, padx=4)
ttk.Label(tab3, text="Weight coefficient for the location-based criteria:    W_loc = 1 - W_area").grid(row=16, column=0, sticky="e", pady=4, padx=4)
e30 = ttk.Entry(tab3, width=5)
e30.grid(row=15, column=1, sticky="w", pady=4, padx=4)
e30.insert(0, "0.5")
ttk.Label(tab3, text="( 0 < W_area < 1 )").grid(row=15, column=2, sticky="w", pady=4, padx=4)
ttk.Separator(tab3, orient='horizontal').grid(row=17, columnspan=6, sticky="ew", pady=4, padx=10)
ttk.Button(tab3, text='Generate report', command=calculateAllIndices, width = 60).grid(row=22, columnspan=6, pady=4, padx=4)

#######
#tab4
#######
ttk.Separator(tab4, orient='horizontal').grid(row=0, columnspan=6, sticky="ew", pady=4, padx=10)
ttk.Label(tab4, text ="Plot", font="Helvetica 11 bold").grid(row=1, columnspan=6, sticky="s", padx=4, pady=4)
ttk.Label(tab4, text="Enter sample no: ").grid(row=2, column=0, sticky="e", pady=4, padx=4)
e40 = ttk.Entry(tab4, width=5)
e40.grid(row=2, column=1, sticky="w", pady=4, padx=4)
e40.insert(0, "1")
ttk.Label(tab4, text="Enter segmentation no: ").grid(row=3, column=0, sticky="e", pady=4, padx=4)
e41 = ttk.Entry(tab4, width=5)
e41.grid(row=3, column=1, sticky="w", pady=4, padx=4)
e41.insert(0, "1")
ttk.Button(tab4, text='Generate plots', command=plotSegments, width = 20).grid(row=4, columnspan=6, pady=4, padx=4)
ttk.Separator(tab4, orient='horizontal').grid(row=5, columnspan=6, sticky="ew", pady=4, padx=10)
ttk.Label(tab4, text ="Save shapefiles", font="Helvetica 11 bold").grid(row=6, columnspan=6, sticky="s", padx=4, pady=4)
ttk.Button(tab4, text='Generate files', command=createPoly, width = 20).grid(row=7, columnspan=6, pady=4, padx=4)
ttk.Separator(tab4, orient='horizontal').grid(row=8, columnspan=6, sticky="ew", pady=4, padx=10)
selected()
root.mainloop() #end
