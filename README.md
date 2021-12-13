# SCREENING AND REPLACING DASHBOARD
For full details about this project, please visit [poster](https://drive.google.com/file/d/1fNlnPiMtFKbRdTZsSSQtDKzEYZNC2gSz/view?usp=sharing),  [report](https://drive.google.com/file/d/1LUnjT9A7Qoyk-koqCE2KcxVEv7fO6A0w/view?usp=sharing)

## Set up  
  1. Download [HECDSS-Vue 3.2.3](https://www.hec.usace.army.mil/software/hec-dssvue/downloads.aspx)
  2. Run  
      ```
      git clone https://github.com/nwm-54/hecdss
      ```
  3. Open grasslands.dss in HECDSS-Vue.
  4. Go to **Tools -> Script Editor** to import dashboard.py file. Click *Save and Test* to run the script
 ## Demo
  Dashboard interface to interact with database <br />
![](/demo_imgs/ref_replace.png "Dashboard interface to interact with database") 
![](/demo_imgs/ref_screen.png "Dashboard interface to interact with database") 

<!--   ![](/demo_imgs/dashboard.png "Dashboard interface to interact with database") -->
<!-- ![](/ref replace.png)
![](/ref screen.png) -->

  
  Screening and replacing missing values/ erroneous value with interpolation 
  ![](/demo_imgs/results.png "Screening and replacing missing values/ erroneous value with interpolation")
  ## Users Guide
  More details about the program provided [here](https://drive.google.com/file/d/1br-OarxMH9SZmHyPylpeuDwZzXV_zHi8/view?usp=sharing)
## Workflow of the program
When the script is run, the program will execute the last **main** function, which will look at the .dss file that is currently in view in HECDSS-Vue main window. <br>
<img src="https://user-images.githubusercontent.com/45931542/145825377-192acca9-de39-47c2-9b84-a4064da25bcf.png"
     alt="Markdown Monster icon"
     style="float: left; margin-right: 10px;" />
</br>
*KerrDam.dss is in used the example below*
At a high level, the program retrieves data from the .dss file, displays data onto the dashboard and allows user to interact with the database through buttons on the dashboard.
Each .dss file contains mutiple records of data indexed by pathname. Each pathname, displayed as a row in HECDSS-Vue main window, is a [TimeSeriesContainer](https://www.hec.usace.army.mil/confluence/dssvuedocs/latest/scripting-dssvue/working-with-datacontainers) Class which contains a table of data points along with other metadata [^1]. The program interact with .dss file by accessing individual pathname, modifying the TimeSeriesContainer object and saving the new data back into .dss file. All of the above steps is done via calling [HECDSS Vue API](https://www.hec.usace.army.mil/confluence/dssvuedocs/latest/scripting-dssvue)

The GUI of the dashboard is done with Swing library: [Jython docs](https://wiki.python.org/jython/SwingExamples) and [Java docs](https://docs.oracle.com/javase/7/docs/api/javax/swing/package-summary.html)

### Program Structure
Functions in the program can be catergoriezed into one of the following types: 
  - Type D: functions that help with **D**isplaying the data onto the dashboard using the Swing library
  - Type T: functions that take in user's interaction and **T**emporarily modify the pathname's data (type I functions to be called after if the user allows the modification to be permanent). In this program, the temporary pathname's data is the class **Data Table Display**.
  - Type I: functions that helps **I**nteract with HECDSS database

Generally speaking, after initalizing the dashboard from the .dss file, type D functions waits for users' click events. Interactions with the dasboard (such as inputting numbers, ticking the boxes, clicking buttons,...) are taken as input to type T functions, which will create a copy of the origonal data and apply the modifications (such as capping the data within a range, removing outliers,...). The new changes is then displayed onto the dashboard with type D functions. If the user proceeds to click *Save as Copy* or *Overwrite*, type I functions would be called to permanently save the changes with HECDSS APIs.

To modify/add functionalities to this program, trace back the code to find which functions are responsible to handle the customized features. If the customized features only involes data displaying (such as plotting data, changing rows and column headers,...), consider looking into type D functions. Similarly, features that involves making temporary changes to data can be made with modifying type T (such as adding new screening techniques) and type I functions.
### Function Type
Functions that are not included in this table are created to help with code readability and debugging the program. 
| Class | Function Name  | Type | Notes |
| ------------- | ------------- | ------------- | ------------- |
| HeaderRenderer | getTableCellRendererComponent | D | overwrites default functions from Swing library - customize the header in **(1)** |
| ColorRenderer | getTableCellRendererComponent | D | overwrites default functions from Swing library - customize the background cell in **(1)** |
| FreezeTableModel | isCellEditable | D | cells in **(1)** are not interactive |
| MyCustomTable | addData | I | create table **(1)** |
| DataTableDisplay | removeEmptyPath | I | removes empty pathname or pathname with error data or else the HECDSS-Vue program could not display data properly - **make sure to call this function after saving pathname to .dss file** |
| | makeQuality | T | marks data points as rejected or replaced for table display |
| | overwrite | I | replaces the original data with the modification data |
| | saveCopy | I | saves the modification data under a new pathname |
| | mergingTscm | T | combines many small interval pathnames to one large interval pathname |
| | fillReplaceIndex | T | creates a list of indexes to be replaced |
| | findPrevValidValue | T | helps with data interpolation - find the previous value datapoint |
| | findNextValidValue | T | helps with data interpolation - find the next value datapoint |
| | replaceLinearTscm | T | replaces data with linear interpolation |
| | replaceCustomTscm | T | replaces data with a custom value |
| | averageValidValue | T | calculates the average of valid data points 
| | replaceAverageTscm | T | replaces data with average of valid data points |
| | removeRejected | T | removes rejected datapoints [^2] |
| | screenTscm | T | takes in input from ... and perform screening accordingly - this function is called when user clicks **Compute** |
| | fillMergedTscm | T | fills data in missing value when combining pathnames together |
| | resetDatatable| T | undos the temporary changes -  called when user clicks **Reset** |
| MainFrame_revised | makeStationTree | D | generates the pane **(2)** |
| | updateTree | D | rerenders pane **(2)** when new pathname is added |
| | makeStationInfoPane | D | creates tab for each pathname **(3)** |
| | addReplaceTab | D | generates replace tab **(4)** |
| | onReplaceMethod | D | collects input regarding user's choice of replace method |
| | onComputeReplace | D | handles the computation when user clicks **Compute** on replacing tab |
| | addTablePane | D | generates the table pane - including **(1)**, **(5)**, and the bottom buttons |
| | updateReportTextField | D | updates **(6)** |
| | onReset | D | handles the event of user clicking **Reset** | 
| | onOverwrite | D | handles the event of user clicking **Overwrite** |
| | onSaveCopy | D | handles the event of user clicking **Save as Copy** |
| | onPlotParam | D | handles the event of user clicking **Plot** | 
| | onTypeChangeLimit | D | collects user's choice of Change Limit "Percentage" or "AvgDiff" |
| | addScreenConditions | D | adds screening conditions | 
| | addScreenTab | D | generates screening tab **(5)** | 
| | onCheckBoxConditions | D | collects user's choice of screening condition |
| | displayOriginalColumn | D | display original column in table **(1)** | 
| | displayColumn | D | display column in table **(1)** |
| | onComputeScreen | D | handles the event of user clicking **Compute** on screening tab | 
| | getScreenSpinnerValue | D | collects number values from box **(7)**|
| | getTimeWindowSpinnerValue | D | collects number values from box **(8)**|
| | run | D | displays the dashboard |















[^1]: To view the data of each pathname, follow -> Raw Data
[^2]: Reject datapoints are not deleted but are marked with value of -3.4028234663852886e+38. Datapoint with this values are not displayed and used in calculation
  

