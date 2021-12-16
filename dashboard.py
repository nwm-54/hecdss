# name=dashboard_paramC_update_Aug27
# description=copy from dashboard_param_A_timestamps
# description=change in getPathnameColumn function ~line 1265-ish
# displayinmenu=true
# displaytouser=true
# displayinselector=true
from hec.script import Plot, AxisMarker
from hec.heclib.dss import HecDss, DSSPathname
from javax.swing import *
import java
import struct
import time
from javax.swing import *
from javax.swing.tree import (DefaultTreeCellRenderer, DefaultTreeCellEditor,
                              TreeSelectionModel, TreePath, TreeModel)
from javax.swing.tree import DefaultMutableTreeNode
from javax.swing.event import *
from java.awt.event import ActionListener
from java.awt import *
from hec.heclib.dss import HecDss, DSSPathname
from hec.heclib.util import HecTime
from hec.hecmath import *
from hec.hecmath.functions import TimeSeriesFunctions
from hec import *
from hec.dssgui import ListSelection
from hec.script import Tabulate
from javax.swing.table import DefaultTableModel, DefaultTableCellRenderer
from java.text import DecimalFormat
from javax.swing.border import EtchedBorder

defaultScreenValue_CONST  = {'PH':[6.0,9.0,'pH'],'SPCOND':[150.0, 5000.0, 'uS/m'], 'CONDUCTIVITY':[150.0, 5000.0, 'uS/m'],'DEPTH':[0.0,500.0, 'ft'],'TURBIDITY':[0.0,100.0,'NTU'],'TEMP':[4.44,37.38,'C'],'DO':[1.0,15.0,'mg/L']}
minValue_CONST = -9999.0#0.0
maxValue_CONST = 99999999.00
stepValue_CONST = 0.01	
defaultBackgroundSpinner_CONST = Color(230,230,230)
deactivateBackgroundSpinner_CONST = Color(150,150,150)
missingNumericValue_CONST = -3.4028234663852886e+38 
rejectedQualityIndex = 5
missingQualityIndex = 3
Color_HEADER = Color(240,240,240)
Color_SCREEN = Color(205,0,0)
Color_REPLACE = Color(0,205,0)
Color_GRAY =Color(230,230,230)
Color_WHITE = Color(255,255,255)

'''
HELPER FUNCTIONS
'''
#def setAsRejected(value):
#	return value | (1<< (rejectedQualityIndex-1))

#The following two function set the quality flag for data's quality. More about quality flag: https://www.hec.usace.army.mil/confluence/dssvuedocs/latest/scripting-dssvue/working-with-datacontainers
def set_quality_bit(value, quality_index):
	bit = quality_index-1
    	return value | (1<<bit)

def clear_quality_bit(value, quality_index):
	bit = quality_index-1
   	return value & ~(1<<bit)

#This function takes in a list of pathnames from a file and return a list of continuous pathnames
def get_param_name(pathnames, stationName):
	param_name_list = set()
	for name in pathnames:
		if stationName in name and 'DISCRETE' not in name:
			param_name_list.add(DSSPathname(name).aPart())
	return param_name_list

#This funciton get parameter name from the station info pane tab
def getStationParamName(parent, child):
	index = parent.indexOfComponent(child)
	tabTitle = parent.getTitleAt(index)
	paramName = tabTitle.split('-')[0].strip()
	stationName =  tabTitle.split('-')[-1].strip()
	return stationName, paramName

#This function checks the types of replace value: missing or reject
def replaceFlagSelected(missingReplaceButton, rejectReplaceButton):
	res = ''
	if missingReplaceButton.isSelected():
		res += 'M'
	if rejectReplaceButton.isSelected():
		res += 'R'
	return res

#This function gets the default value for the spinner input
def getDefaultScreenValue(paramName):
	for key in defaultScreenValue_CONST.keys():
		if key in paramName:
			return defaultScreenValue_CONST[key][0],  defaultScreenValue_CONST[key][1],  defaultScreenValue_CONST[key][1]- defaultScreenValue_CONST[key][0], defaultScreenValue_CONST[key][2]
	return minValue_CONST,maxValue_CONST,stepValue_CONST, ''

#This function prints a message to user
def messageDialog(msg):
	JOptionPane.showMessageDialog(None, msg, "Alert Title", JOptionPane.ERROR_MESSAGE)
	
#This functions helps to parse time
def numToStringInterval(number):
			if number<60:
				return str(number)+'MIN'
			elif number<=1440:
				return str(number/60)+'HOUR'
			else:
				return str(number/60/24)+'DAY'
			
#This function split the pathname into sections according to parameter
def getColumnFromBranchName(branchName):
	a, c, e, f = branchName.split('/')
	return a.strip(),c.strip(),e.strip(),f.strip()
#This function shows the confirm dialog to user
def confirmDialog(msg):
	JOptionPane.showMessageDialog(None, msg)
	
def hasTimeWindow(windowTime):
	return windowTime[0].toString() != ''

#This function get the specified part of a pathname
def getPathnameColumn(pathname, column):
	if column =='c': #switch here a to c, c to a
		return DSSPathname(pathname).aPart()
	elif column =='b':
		return DSSPathname(pathname).bPart()
	elif column =='a': #switch here a to c, c to a
		return DSSPathname(pathname).cPart()
	elif column =='d':
		return DSSPathname(pathname).dPart()
	elif column =='e':
		return DSSPathname(pathname).ePart()
	else:
		return DSSPathname(pathname).fPart()
	
#This function generates a dictionary of all pathname along with its metadata
def getStationDict(fileName):
	dssFile = HecDss.open(fileName)
	stationName = set()
	for pathname in dssFile.getPathnameList():
		if 'DISCRETE' not in pathname and 'IR-' not in pathname:
			stationName.add(getPathnameColumn(pathname,'b'))
	stationDict = {}
	for sname in stationName:
		print('making station dict',sname)
		paramsName = getAllParamNameByStation(fileName, sname)
		stationDict[sname] = {}
		stationDict[sname]['paramNameList'] = paramsName
		
		for pname in paramsName:
			print('making station dict param',pname)
			stationDict[sname][pname] = {}
			stationDict[sname][pname]['display'] = False
			dataTable = DataTableDisplay(fileName, sname, pname)
			stationDict[sname][pname]['orgDataTable'] = dataTable 
			stationDict[sname][pname]['numValues'] = dataTable.numValues
			stationDict[sname][pname]['missingIndex'] = dataTable.getMissingIndex()
	dssFile.close()
	print('done making station dict')
	return stationDict

#This function updates values for the station dictionary
def updateStationDict(fileName,  stationDict, sname, pname):
	stationDict[sname][pname] = {}
	stationDict[sname][pname]['display'] = False
	dataTable = DataTableDisplay(fileName, sname, pname)
	stationDict[sname][pname]['orgDataTable'] = dataTable 
	stationDict[sname][pname]['numValues'] = dataTable.numValues
	stationDict[sname][pname]['missingIndex'] = dataTable.getMissingIndex()
	return stationDict

#This functions gets all pathnames of a station.	
def getAllParamNameByStation(fileName, stationName):
	dssFile = HecDss.open(fileName)
	paramName = set()
	for pathname in dssFile.getPathnameList():
		if getPathnameColumn(pathname,'b') == stationName and 'DISCRETE' not in pathname and 'IR-' not in pathname:
			newParam = getPathnameColumn(pathname,'a') + '/'+getPathnameColumn(pathname,'c')+'/' +  getPathnameColumn(pathname,'e') +'/' +  getPathnameColumn(pathname,'f') 
			paramName.add(newParam)
	dssFile.close()
	return paramName

	
'''
The following classes allow customization of the GUI of the dashboard and is not affect the functionalities of the program
'''		
class HeaderRenderer(DefaultTableCellRenderer ):
	def __init__(self ):
		DefaultTableCellRenderer.__init__(self)
		self.setHorizontalAlignment(JLabel.CENTER)
		
	def getTableCellRendererComponent(self,table, value, isSelected, hasFocus, row, column):
		cell = super(self.__class__, self).getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
		cell.setBackground(Color_HEADER)
		cell.setBorder(BorderFactory.createEtchedBorder(EtchedBorder.LOWERED))
		cell.setForeground(Color.BLACK)
		return cell

		
class ColorRenderer(DefaultTableCellRenderer ):
	def __init__(self, modifiedIndex=[],  customColor= Color_GRAY, defaultColor= Color_GRAY, numDecimal=2 ):
		DefaultTableCellRenderer.__init__(self)
		if numDecimal==0:
			self.decimalFormatter = DecimalFormat('#')
		elif numDecimal==1:
			self.decimalFormatter = DecimalFormat('#.0')
		else : #if numDecimal==2:
			self.decimalFormatter = DecimalFormat('#.00')
		self.defaultColor = defaultColor
		self.customColor = customColor
		self.setHorizontalAlignment(JLabel.RIGHT)
		self.modifiedIndex = modifiedIndex
		
	def getTableCellRendererComponent(self,table, value, isSelected, hasFocus, row, column):
		if  isinstance(value, float):
			if value == missingNumericValue_CONST:
				value = None
			else:
				value = self.decimalFormatter.format(float(value))
		cell = super(self.__class__, self).getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
		if row in self.modifiedIndex:	
			cell.setBackground(self.customColor)
		else:
			cell.setBackground(self.defaultColor)
		cell.setForeground(Color.BLACK)
		return cell
		
class FreezeTableModel(DefaultTableModel):
	def isCellEditable(self):
		return False

class MyCustomTable():
	def __init__(self, numDecimal):
		self.table = None
		self.data = [] 
		self.screenCol = None
		self.replaceCol = None
		self.rejectedCell = None
		self.replaceCell = None
		self.numDecimal = numDecimal
	def addData(self, columnName,  tsc, rejectedCell=[], replaceCell=[]):
		if self.table==None:
			header = ['ORDINATE', 'DATETIME', columnName.upper()]
			hecTime = HecTime()
			for i in range(tsc.numberValues):
				hecTime.set(tsc.times[i])
				time_str = hecTime.toString()
				self.data.append([i+1, time_str, tsc.values[i]])
			self.table = JTable(FreezeTableModel(self.data, header))
			self.table.setRowSelectionAllowed(False)
			self.table.setColumnSelectionAllowed(False)
			self.table.getTableHeader().setDefaultRenderer(HeaderRenderer())
			self.table.getTableHeader().setPreferredSize( Dimension(60,30))
		else:
			self.table.getModel().addColumn( columnName.upper(), list(tsc.values))
			if columnName.upper() == 'SCREEN':
				self.screenCol = self.table.getModel().getColumnCount() -1
				self.rejectedCell = rejectedCell
			elif columnName.upper() == 'REPLACE':
				self.replaceCol = self.table.getModel().getColumnCount() -1
				self.replaceCell = replaceCell
			else:
				raise ValueError('Table heading is not valid')
				
		numCol = self.table.getModel().getColumnCount()
		for i in range(numCol):		
			if i<numCol-1: #all column except the last column
				if i==self.screenCol: 
					colorRenderer = ColorRenderer(modifiedIndex=self.rejectedCell, customColor=Color_SCREEN, numDecimal=self.numDecimal)
				elif i== self.replaceCol: 
					colorRenderer = ColorRenderer(modifiedIndex=self.replaceCell, customColor=Color_REPLACE,  numDecimal=self.numDecimal)
				else:
					colorRenderer = ColorRenderer()
				col = self.table.getColumnModel().getColumn(i);
				col.setCellRenderer(colorRenderer)
			else: #last column
				if i== self.screenCol:
					colorRenderer = ColorRenderer(modifiedIndex=self.rejectedCell, customColor=Color_SCREEN, defaultColor=Color_WHITE, numDecimal=self.numDecimal)
				elif i == self.replaceCol:
					colorRenderer = ColorRenderer(modifiedIndex=self.replaceCell, customColor=Color_REPLACE, defaultColor=Color_WHITE, numDecimal=self.numDecimal)
				else:
					colorRenderer = ColorRenderer(defaultColor=Color_WHITE)
				col = self.table.getColumnModel().getColumn(i);
				col.setCellRenderer(colorRenderer)
			if i==0: #ordinate column
				self.table.getColumnModel().getColumn(i).setPreferredWidth(100)
			elif i==1: #datetime column
				self.table.getColumnModel().getColumn(i).setPreferredWidth(250)
			else: #value column
				self.table.getColumnModel().getColumn(i).setPreferredWidth(150)
		
	def getTable(self):
		return self.table

''''
This class creates a temporary copy of the original data that the user can use and make changes to. 
This copied version is displayed onto the dashboard as the user performs screening/replacing values, 
but it would not be save into the database until the users takes action. 
'''
class DataTableDisplay():
	def __init__(self, fileName, stationName, paramName):
		self.fileName = fileName
		self.stationName = stationName
		self.paramName = paramName
		self.param, self.cPart, self.time, self.fPart =getColumnFromBranchName(self.paramName) 

		self.missingIndex = []
		self.rejectedIndex = []
		self.replaceIndex = []
		self.missingBool = None
		self.orgTscm = self.mergingTscm()
		self.modifiedTscm = self.orgTscm.copy()
		self.numValues =  self.modifiedTscm.getData().numberValues
		self.rejectedBool = [False for _ in range(self.numValues)]

	#These folowing 3 functions helps to display the number of missing values, replaced values and rejected values onto the dashboard
	def getStringMissing(self):
		return '%s/%s'%(len(self.missingIndex), self.modifiedTscm.getData().numberValues)
	def getStringRejected(self):
		return '%s/%s'%(len(self.rejectedIndex), self.modifiedTscm.getData().numberValues)
	def getStringReplaced(self):
		return '%s/%s'%(len(self.replaceIndex), self.modifiedTscm.getData().numberValues)

	#This function removes empty pathname in file. MUST CALL after save.
	def removeEmptyPath(self): #must call after saving
		dssFile = HecDss.open(self.fileName)
		pathnameList = dssFile.getPathnameList()
		for path in pathnameList:
			tsc = dssFile.get(path)
			if tsc.numberValues == 0: #empty pathname
				dssFile.delete([path])
				print('delete ', path)
		dssFile.close()
		
	#This functions creates quality flags for new data
	def makeQuality(self, org_quality):
		if org_quality is None:
			org_quality = [0 for _ in range(len(self.rejectedBool))]
		new_quality = []
		for i in range(len(org_quality)):
			val = org_quality[i]
			if self.rejectedBool[i]: 
				val = set_quality_bit(val, 5)
			elif not self.missingBool[i]:
				val = set_quality_bit(val,1)
			new_quality.append(val)
		return new_quality
	
	#As user choose to overwrite the original data with the temporary data, this function helps to save the new data into the original pathname 
	# - Hence overwriting
	def overwrite(self):
		dssFile = HecDss.open(self.fileName)
		modifiedTsc = self.modifiedTscm.getData().clone()
		modifiedTsc.quality = self.makeQuality(modifiedTsc.quality)
		modifiedTsc.fullName =  "/%s/%s/%s//%s/%s/" % (self.param, self.stationName, self.cPart,self.time, self.fPart)
		print(modifiedTsc.fullName)
		dssFile.put(modifiedTsc)
		dssFile.close()
		self.removeEmptyPath()
		confirmDialog('Dataset saved ')
		stationName = self.stationName
		pathname = modifiedTsc.fullName
		paramName = getPathnameColumn(pathname,'a') + '/'+getPathnameColumn(pathname,'c')+'/' +  getPathnameColumn(pathname,'e') +'/' +  getPathnameColumn(pathname,'f') 
		return stationName, paramName
		
	#This function saves the new data as a copy of the original data.
	def saveCopy(self):
		dssFile = HecDss.open(self.fileName)
		toSaveTscm, _ = self.removeRejected()
		modifiedTsc = toSaveTscm.getData().clone()
		cur_timestamp = int(time.time())
		modifiedTsc.fullName =  "/%s/%s/%s//%s/%s/" % (self.param, self.stationName, self.cPart,self.time, self.fPart+' MODIFIED ' + str(cur_timestamp))
		pathname = modifiedTsc.fullName

		print(modifiedTsc.fullName)
		dssFile.put(modifiedTsc)
		dssFile.close()
		self.removeEmptyPath()
		confirmDialog('New dataset saved as '+modifiedTsc.fullName)

		stationName = self.stationName
		paramName = getPathnameColumn(pathname,'a') + '/'+getPathnameColumn(pathname,'c')+'/' +  getPathnameColumn(pathname,'e') +'/' +  getPathnameColumn(pathname,'f') 

		return stationName, paramName
	
	#This function checks the quality flag to see if the data value is missing
	def isMissing(self, value):
		value = int(value) >> (missingQualityIndex-1)
		return value&1
	
	#This function checks the quality flag to see if the data value is rejected
	def isRejected(self, value):
		value = value >> (rejectedQualityIndex-1)
		return value&1
	
	def getMergedTscm(self):
		return self.orgTscm
	
	#This function merges two TSC together, filled the empty range with null values.
	def mergingTscm(self):
		dssFile = HecDss.open(self.fileName)
		allPathname = dssFile.getPathnameList()
		mergedTscm = None
		i = 0
		first_tscm = True

		while i<len(allPathname):
			if self.stationName==getPathnameColumn(allPathname[i], 'b')  and self.param==getPathnameColumn(allPathname[i], 'a')  and self.time==getPathnameColumn(allPathname[i], 'e') and self.cPart==getPathnameColumn(allPathname[i],'c')  and self.fPart==getPathnameColumn(allPathname[i],'f') :

				if first_tscm:
					mergedTscm = dssFile.read(allPathname[i])
					orgInterval = mergedTscm.getData().interval
					first_tscm = False
				else:
					tscm = dssFile.read(allPathname[i])
					mergedTscm = mergedTscm.mergeTimeSeries(tscm)

				
			i += 1
		
		mergedTscm.setData(self.fillMergedTscm(mergedTscm, orgInterval)) # mergeTscQuality,
		dssFile.close()
		return mergedTscm
		
	#This function returns a list of index that need to be replaced
	def fillReplaceIndex(self, replaceFlag, timeIdx=None):
		print('fill replace ', replaceFlag, timeIdx)
		replaceIndex = []
		if 'R' in replaceFlag:
			replaceIndex.extend(self.rejectedIndex)
		if 'M' in replaceFlag:
			replaceIndex.extend(self.missingIndex)
		if timeIdx is not None:
			fillter_replaceIndex = []
			for idx in replaceIndex:
				if idx>=timeIdx[0] and  idx<timeIdx[1]:
					fillter_replaceIndex.append(idx)
			return fillter_replaceIndex
		return replaceIndex
		
	#This function finds the immediate previous valid value -> to find start point of interpolation
	def findPrevValidValue(self, index):
		while index >=0 and ( index in self.rejectedIndex or index in self.missingIndex):
			index  -=1
		if index<0:
			value =  self.averageValidValue()
		else: #found a valid value precede the index
			value = self.modifiedTscm.getData().values[index]
		return  value
	
	#This function finds the immediate next valid value -> to find end point of interpolation
	def findNextValidValue(self, index):
		while index<self.modifiedTscm.getData().numberValues and ( index in self.rejectedIndex or  index in self.missingIndex):
			index +=1
		if index==self.modifiedTscm.getData().numberValues:
			value =  self.averageValidValue()
		else: #found a valid value succeed the index
			value = self.modifiedTscm.getData().values[index]		
		return  value
		
	#This function replaces the data at replaced index with linear interpolation
	def replaceLinearTscm(self,  replaceFlag,timeIdx ):
		self.replaceIndex = self.fillReplaceIndex(replaceFlag,timeIdx)
		newTsc = self.modifiedTscm.getData().clone()
		timeWindow = []
		i=0

		while i<len(self.replaceIndex): 
			timeWindow.append(self.replaceIndex[i])
			j=i
			while j<len(self.replaceIndex)-1 and self.replaceIndex[j+1]-self.replaceIndex[j]==1:
				j+=1
				
			timeWindow.append(self.replaceIndex[j])
			i=j+1
		print('timeWindow', timeWindow)	

		for i in range(0, len(timeWindow), 2):
			startIndex, endIndex =timeWindow[i],timeWindow[ i+1]
			fromValue, toValue = self.findPrevValidValue(startIndex), self.findNextValidValue(endIndex)
			increment = (toValue-fromValue)/(endIndex-startIndex+2)
			currentValue = fromValue+increment
			for j in range(startIndex, endIndex+1):
				newTsc.values[j] = currentValue
				currentValue += increment
		self.modifiedTscm.setData(newTsc)
		return self.modifiedTscm, self.replaceIndex

	#This function replaces the data at replaced index with custom value
	def replaceCustomTscm(self,  replaceFlag, customValue, timeIdx):
		self.replaceIndex = self.fillReplaceIndex(replaceFlag, timeIdx)
		newTsc = self.modifiedTscm.getData().clone()
		for index in self.replaceIndex:
			newTsc.values[index] = customValue
		self.modifiedTscm.setData(newTsc)
		return self.modifiedTscm, self.replaceIndex
	
	#This function checks if the TSC has no valid value at all
	def hasValidValue(self):
		numberValues = self.modifiedTscm.getData().numberValues
		number_rejectedIndex =  len(self.fillReplaceIndex('MR'))
		return  numberValues != number_rejectedIndex
	
	#This function computes the average of VALID values - excludes invalid value
	def averageValidValue(self):
		newTsc = self.modifiedTscm.getData().clone()
		sumValues = 0# sum(newTsc.values) 
		count = 0
		for i in range(len(newTsc.values)):
			if newTsc.values[i] != missingNumericValue_CONST :
				sumValues += newTsc.values[i]
				count += 1

		if count == 0:
			return None
		return  sumValues/count
		
	#This function replaces values with the average of valid data
	def replaceAverageTscm(self, replaceFlag,timeIdx):
		self.replaceIndex =self.fillReplaceIndex(replaceFlag,timeIdx)
		startIdx, endIdx = timeIdx
		avgValue = self. avgValid(startIdx, endIdx)
		newTsc = self.modifiedTscm.getData().clone()
		for index in self.replaceIndex:
			newTsc.values[index] = avgValue
		self.modifiedTscm.setData(newTsc)
		return self.modifiedTscm, self.replaceIndex
		
	def getReplaceIndex(self):
		return self.replaceIndex


	def avgValid(self, startIdx, endIdx):
		tsc = self.modifiedTscm.getData().values
		total, cnt=0,0
		for i in range(startIdx, endIdx):
			if not self.rejectedBool[i] and not self.missingBool[i]:
				total += tsc[i]
				cnt +=1
		return total/cnt
	#This function removes the rejected value - replace with null value
	def removeRejected(self, timeIdx=None,  customValue = missingNumericValue_CONST ): #based on replaceCustomValue
		newTsc = self.modifiedTscm.getData().clone()
		cnt = 0
		if timeIdx is None:
			startIdx, endIdx =0,  newTsc.numberValues
		else:
			startIdx, endIdx = timeIdx
		for i in range(startIdx, endIdx):
			if self.rejectedBool[i]:
				cnt +=1
				newTsc.values[i] = customValue
		assert cnt == len(self.rejectedIndex), 'bool ' + str(cnt)+'and rejectedIndex '+  str(len(self.rejectedIndex) )+' does not have equal length'
		self.modifiedTscm.setData(newTsc)
		return self.modifiedTscm, self.rejectedIndex
		
	#This function performs screening on the TSC with the selected method of screening and the ordinate
	def screenTscm(self, minValue, maxValue, changeLimit, timeIdx, pointsSpan, typeChangeLimit = 'absDiff'):
		#adding timeWindow
		startIdx, endIdx = timeIdx
		lastMovAvg = 1e-8
		func = lambda x,y: abs(x-y)
		if typeChangeLimit != 'absDiff': #percentage
			changeLimit /= 100
			func = lambda x,y: abs(x-y)/x
		tsc = self.modifiedTscm.getData().values
		#reject with min max
		for i in range(startIdx, endIdx, 1): 
			if not self.missingBool[i] and (tsc[i]<minValue or tsc[i]>maxValue): #or (i-1>0 and abs(tsc[i]-tsc[i-1])>changeLimit):
				self.rejectedIndex.append(i)
				self.rejectedBool[i] = True
		#reject with changelimit
		avg_valid = self.avgValid(startIdx, endIdx)
		
		avg_window = [avg_valid for _ in range(int(pointsSpan))]
		prev_total = sum(avg_window)/pointsSpan
		print('AVG WINDOW', avg_window)
		print('PREV TOTAL', prev_total)
		print('CHANGE LIMIT', changeLimit)
		for i in range(startIdx, endIdx, 1): 
			if not self.missingBool[i] and not self.rejectedBool[i]:
				total = ( sum(avg_window[1:])+tsc[i] )/ pointsSpan
				if total == 0.0:
					total += 1e-10
				if func(prev_total, total)>changeLimit:
					self.rejectedBool[i] = True
					self.rejectedIndex.append(i)
				else:
					prev_total = total
				
		return self.modifiedTscm, self.rejectedIndex
		
	def getRejectedIndex(self):
		return self.rejectedIndex
		
	def getMissingIndex(self):
		return self.missingIndex

	#This function fills the empty range with null value - use for merging TSC
	def fillMergedTscm(self,  tscm, orgInterval, fillValue= -9999999.99): #mergeTscQuality
		tsc = tscm.getData()
		hectime = HecTime()
		dummyTscmList = []
		
		for i in range(len(tsc.times[:-1])):
			hectime.set(tsc.times[i])
			if  tsc.times[i+1]-tsc.times[i] > orgInterval*2: #at least one datum is missing
				#create dummy tscm
				startTime = HecTime()
				startTime.set(tsc.times[i]+orgInterval)
				endTime = HecTime()
				endTime.set(tsc.times[i+1]-orgInterval)

				dummyTscm = TimeSeriesMath.generateRegularIntervalTimeSeries(startTime.toString(),endTime.toString(), numToStringInterval(orgInterval), None, fillValue)
				dummyTsc = dummyTscm.getData().clone()
				dummyTsc.quality = [int(0) for _ in range(dummyTsc.numberValues)]
				dummyTscm.setData(dummyTsc)
				dummyTscmList.append(dummyTscm)

		for dummyTscm in dummyTscmList:
			tscm = tscm.mergeTimeSeries(dummyTscm)
		dummyTsc =  tscm.getData().clone()
		for i, value in enumerate(tscm.getData().values):
			if value == fillValue: #self.isMissing(value):
				dummyTsc.values[i] = missingNumericValue_CONST
		if self.missingBool is None:
			self.missingBool = [False for _ in range(tscm.getData().numberValues)]
		for i, value in enumerate(tscm.getData().values):
			if  dummyTsc.values[i] ==missingNumericValue_CONST:
				self.missingIndex.append(i)
				self.missingBool[i] = True

		tscm.setData(dummyTsc)
		return tscm.getData()
		
	#This functions erases the changes to the data return to the original data
	def resetDataTable(self):
		self.rejectedIndex = []
		self.replaceIndex = []
		self.modifiedTscm = self.orgTscm.copy()
		self.missingBool = [False for _ in range(self.numValues)]
		self.rejectedBool = [False for _ in range(self.numValues)]

'''
This class handles the start and end coordinate that the user wishes to make changes to - default as the entire dataset.
'''
class TimeIdx():
	def __init__(self, spinner):
		self.timeIdx = [s.getValue()-1 for s in spinner]#change from Ordinate to Index
		if self.isValidRange():
			self.timeIdx[-1]+=1 # make endIdx non-inclusive
	def getTimeIdx(self): #[0,10] or [[0,10],[10,20]]
		return self.timeIdx
	def isValidRange(self):
		if self.timeIdx[1]<self.timeIdx[0]:
			messageDialog('End Ordinate must be larger than Start Ordinate. Click Reset.')
			return False
		return True
		
'''
This class generates the dashboard of the program: combining both the GUI classes and the DataTableDisplay temporary data.
'''
class MainFrame_revised():
	def __init__(self, fileName, windowTime):
		self.fileName = fileName
		self.hasTimeWindow = True
		if not hasTimeWindow(windowTime):
			self.hasTimeWindow = False
			print(windowTime)
		#MAIN FRAME
		self.mainFrame = JFrame(self.fileName, layout=BorderLayout(), size=(700,800))
		self.mainFrame.setLocation(300,100)
		
		self.stationDict = getStationDict(self.fileName)
		self.computeScreenClicked = False
		self.computeReplaceClicked = False
		
		#SPLITPANE  TREE AND TABBEDPANE
		#JTREE
		self.stationsTree = self.makeStationsTree()

		#TABBEDPANE
		self.stationInfoPane = JTabbedPane()
		#SPLITPANE
		
		self.mainPane = JSplitPane(JSplitPane.HORIZONTAL_SPLIT,self.stationsTree, self.stationInfoPane)
		self.mainFrame.add(self.mainPane)
	
	#This function generates the station JTree on the left of the Splitted Pane
	def makeStationsTree(self):
		root = DefaultMutableTreeNode('Stations')
		for stationName in self.stationDict.keys():
			stationBranch = DefaultMutableTreeNode(stationName)
			root.add(stationBranch)
			for paramName in self.stationDict[stationName]['paramNameList']:
				stationBranch.add(DefaultMutableTreeNode(paramName))
		stationsTree = JTree(root, valueChanged = self.selectParamFromTree)
		stationsTree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION)
		return stationsTree
	#This function updates the tree as new pathname is added to the tree. 
	def updateTree(self, stationName, paramName, mode):
		root = self.stationsTree.getModel().getRoot()
		child_cnt = self.stationsTree.getModel().getChildCount(root)
		
		for i in range(child_cnt):
			branch = root.getChildAt(i)
			if branch.toString() == stationName:
				print('found branch ')
				child = DefaultMutableTreeNode(paramName)
				if mode=='copy':
					self.stationsTree.getModel().insertNodeInto(child, branch, branch.getChildCount())
				break
		stationsTree = JTree(root, valueChanged = self.selectParamFromTree)
		stationsTree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION)
		return stationsTree

	#This function handles the event of user clicks on a pathname in the tree
	def selectParamFromTree(self, event):
		tree = event.getSource()
		if tree.getSelectionCount() :
			paramName = tree.getLastSelectedPathComponent() 
		self.makeStationInfoPane(self.stationInfoPane, str(paramName.getParent()), str(paramName))
		
	#This function generatetes the station info tab for each pathname.
	def makeStationInfoPane(self, parentTabbedPane, stationName, paramName):
		if not self.stationDict[stationName][paramName]['display']:
			self.stationDict[stationName][paramName]['display'] = True
			stationTopPane = JTabbedPane()
			self.addScreenTab(stationTopPane, stationName, paramName)
			self.addReplaceTab(stationTopPane, stationName, paramName)
			stationBottomPane = JPanel()
			self.addTablePane( stationBottomPane, stationName, paramName)

			stationPane = JPanel()
			stationPane.setLayout(BoxLayout(stationPane, BoxLayout.Y_AXIS))
			stationPane.add(stationTopPane)
			stationPane.add(stationBottomPane)
			displayName = paramName + ' - ' + stationName
			parentTabbedPane.addTab(displayName, stationPane)

			tabLabel = JPanel()
			tabLabel.add(JLabel(displayName ))
			tabLabel.add(JButton("x" , actionPerformed=self.closeTab))
			tabIndex = parentTabbedPane.getTabCount()
			parentTabbedPane.setTabComponentAt(tabIndex-1,tabLabel)
		else:
			messageDialog('Parameter is already displayed')
			
	#This functions handles the event of closing the station info pane - i.e: allowing shut down of the individual pathname tab and not the whole program
	def closeTab(self, event):
		selected = event.getSource().getParent()
		index = self.stationInfoPane.indexOfTabComponent(selected)
		tabTitle = self.stationInfoPane.getTitleAt(index)
		paramName = tabTitle.split('-')[0].strip()
		stationName =  tabTitle.split('-')[-1].strip()
		self.stationInfoPane.remove(index)
		self.stationDict[stationName][paramName]['display'] = False
		
	#This functions generates the GUI for the replacing task
	def addReplaceTab(self, parentTabbedPane, stationName, paramName):
		replacePane = JPanel()

		replacePane.setLayout(BoxLayout(replacePane, BoxLayout.Y_AXIS))
		c = GridBagConstraints()		

		#merge flag and method into one panel
		c.anchor =  GridBagConstraints.WEST 
		replaceBottomPanel = JPanel()
		replaceBottomPanel.setLayout( GridBagLayout() )
		replaceBottomPanel.setBorder( BorderFactory.createTitledBorder("Options") )
		
		#add time window option
		startOrdinate_DEFAULT= 1
		endOrdinate_DEFAULT = self.stationDict[stationName][paramName]['numValues']
		print('endOrdinate:  ', endOrdinate_DEFAULT)
		c.gridx, c.gridy= 0, 0 #x,y
		ordinate_label = JLabel("<html><b>Ordinate</b>")
		replaceBottomPanel.add(ordinate_label, c)
		c.gridx, c.gridy= 0, 1 #x,y
		start_time_label =  JLabel("<html>Start")
		replaceBottomPanel.add(start_time_label, c)
		c.gridx, c.gridy= 1, 1 #x,y
		start_time_model = SpinnerNumberModel(startOrdinate_DEFAULT,startOrdinate_DEFAULT ,endOrdinate_DEFAULT,1) #default value as 0 ordinate
		start_time_spinner = JSpinner(start_time_model)
		replaceBottomPanel.add(start_time_spinner, c)
		c.gridx, c.gridy= 0, 2 #x,y
		end_time_label = JLabel("<html>End")
		replaceBottomPanel.add(end_time_label, c)
		c.gridx, c.gridy= 1, 2 #x,y
		end_time_model = SpinnerNumberModel(endOrdinate_DEFAULT,startOrdinate_DEFAULT,endOrdinate_DEFAULT,1) #default value as end ordinate
		end_time_spinner = JSpinner(end_time_model)
		replaceBottomPanel.add(end_time_spinner, c)
		self.stationDict[stationName][paramName]['timeWindowReplaceSpinner'] = [start_time_spinner, end_time_spinner]
		
		flag_label = JLabel("<html><b>Flag</b>")
		c.gridx, c.gridy= 2, 0
		replaceBottomPanel.add(flag_label,c)
		missingReplaceButton = JCheckBox("M(missing)")
		c.gridx, c.gridy= 2, 1
		replaceBottomPanel.add(missingReplaceButton,c)
		rejectReplaceButton = JCheckBox("R(rejected)")
		c.gridx, c.gridy= 2, 2
		replaceBottomPanel.add(rejectReplaceButton,c)
		method_label =JLabel("<html><b>Method</b>")
		c.gridx, c.gridy= 3, 0
		replaceBottomPanel.add(method_label,c)
		replace_method = ''
		linearButton = JRadioButton("Linear Interpolation", actionPerformed = self.onReplaceMethod)
		c.gridx, c.gridy= 3, 1
		replaceBottomPanel.add(linearButton,c)
		avgButton = JRadioButton("Average Value", actionPerformed = self.onReplaceMethod)
		c.gridx, c.gridy= 3, 2
		replaceBottomPanel.add(avgButton,c)
		customButton = JRadioButton("Custom Value", actionPerformed = self.onReplaceMethod)
		model = SpinnerNumberModel(0.0,minValue_CONST ,maxValue_CONST,stepValue_CONST)
		customValue = JSpinner(model)
		customValue.setEnabled(False)
		replacemethodGroup = ButtonGroup()
		replacemethodGroup.add(linearButton)
		replacemethodGroup.add(avgButton)
		replacemethodGroup.add(customButton)
		c.gridx, c.gridy= 3, 3
		replaceBottomPanel.add(customButton,c)
		c.gridx, c.gridy= 4, 3
		replaceBottomPanel.add(customValue,c)


		
		self.stationDict[stationName][paramName]['replaceFlagOptions'] = [missingReplaceButton, rejectReplaceButton]
		self.stationDict[stationName][paramName]['replaceMethodOptions'] = [linearButton, avgButton, customButton, customValue]
		computeReplaceButton = JButton("Compute", actionPerformed = self.onComputeReplace, alignmentX = Component.CENTER_ALIGNMENT)
		self.stationDict[stationName][paramName]['computeReplaceButton'] = computeReplaceButton

		replacePane.add(replaceBottomPanel)
		replacePane.add(computeReplaceButton)

		scroll = JScrollPane()
		scroll.setViewportView(replacePane)
		parentTabbedPane.addTab('Replace', scroll)
		
	#This function collects user's input of replacing
	def onReplaceMethod(self, event):

		#Add scroll pane
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent().getParent().getParent()#RadioButton->replaceBottomPanel->replacePane->stationTopPane->StationInfoPane

		stationPane = event.getSource().getParent().getParent().getParent().getParent().getParent().getParent()
		print(stationInfoPane)
		print(stationPane)
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)	
		
		linearButton, avgButton, customButton, customValue = self.stationDict[stationName][paramName]['replaceMethodOptions']
		orgDataTable =  self.stationDict[stationName][paramName]['orgDataTable']
		if linearButton.isSelected():
			replace_method= 'linear'
			customValue.setEnabled(False)
			if not orgDataTable.hasValidValue():
				messageDialog('Dataset has no valid value')
				self.stationDict[stationName][paramName]['computeReplaceButton'].setEnabled(False)
			else:
				self.stationDict[stationName][paramName]['computeReplaceButton'].setEnabled(True)
		if avgButton.isSelected():
			replace_method= 'average'
			customValue.setEnabled(False)
			print ('before checking4')
			if not orgDataTable.hasValidValue():
				print ('check has valid data')
				messageDialog('Dataset has not valid value')
				self.stationDict[stationName][paramName]['computeReplaceButton'].setEnabled(False)
			else:
				self.stationDict[stationName][paramName]['computeReplaceButton'].setEnabled(True)
		if customButton.isSelected():
			replace_method= 'custom'
			customValue.setEnabled(True)
			self.stationDict[stationName][paramName]['computeReplaceButton'].setEnabled(True)
		self.stationDict[stationName][paramName]['replaceMethodSelected'] = replace_method
		print('replaceMethodselected save here ', stationName, paramName, replace_method)
		
	#This function handles the event of user's clicks on the compute button for replacing task
	def onComputeReplace(self, event):

		#Add scroll pane
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent().getParent()#RadioButton->replaceBottomPanel->replacePane->stationTopPane->StationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent().getParent()
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		print('on ComputeReplace ', stationName, '   ', paramName)
		param, cPart, time, fPart = getColumnFromBranchName(paramName)  #paramName.split('/')

		missingReplaceButton, rejectReplaceButton = self.stationDict[stationName][paramName]['replaceFlagOptions']
		replaceFlag = replaceFlagSelected(missingReplaceButton, rejectReplaceButton) 
		orgDataTable =  self.stationDict[stationName][paramName]['orgDataTable']

		print(self.stationDict[stationName][paramName]['replaceMethodSelected']) #TODO is not rejected already
		if self.stationDict[stationName][paramName].has_key('replaceMethodSelected') and len(replaceFlag) != 0:
			#get timestamps
			timeIdx_obj =  TimeIdx(self.stationDict[stationName][paramName]['timeWindowReplaceSpinner'])
			timeIdx = timeIdx_obj.getTimeIdx()
			print('from onComputeReplace ',timeIdx)
			
			self.stationDict[stationName][paramName]['computeReplaceButton' ].setEnabled(False)
			replaceMethod = self.stationDict[stationName][paramName]['replaceMethodSelected']
			if replaceMethod == 'linear':
				screenTscm, replaceIndex = orgDataTable.replaceLinearTscm(replaceFlag,timeIdx)
			elif replaceMethod == 'average':
				screenTscm, replaceIndex = orgDataTable.replaceAverageTscm(replaceFlag,timeIdx)
			else: 
				customValueSpinner = self.stationDict[stationName][paramName]['replaceMethodOptions'][-1] 
				screenTscm, replaceIndex = orgDataTable.replaceCustomTscm(replaceFlag, customValueSpinner.getValue(),timeIdx)

			self.stationDict[stationName][paramName]['replaceIndex'] = replaceIndex
			self.stationDict[stationName][paramName]['modifiledTscm'] = screenTscm
			
			myTable = self.stationDict[stationName][paramName]['myTable']

			myTable.addData('Replace', screenTscm.getData(), replaceCell=replaceIndex)
			self.updateReportTextField(stationName, paramName)

			self.stationDict[stationName][paramName]['myTable'] = myTable
		else: 
			messageDialog('Replace Method or Replace Flag is empty')
	#This function determines the number of decimal places for parameters
	def getNumDecimal(self, paramName):
		if 'COND' in paramName or 'TURBIDITY' in paramName:
			numDecimal=0
		elif 'PH' in paramName:
			numDecimal=1
		else:
			numDecimal=2
		return numDecimal
	
	#This function generates the Table Pane to display data
	def addTablePane(self, parentPane, stationName, paramName):
		tablePane = JPanel()
		tablePane.setLayout(BoxLayout(tablePane, BoxLayout.Y_AXIS))

		orgDataTable = self.stationDict[stationName][paramName]['orgDataTable'] 
		tscm = orgDataTable.getMergedTscm()
		
		self.tableTopPane = JPanel()
		numDecimal = self.getNumDecimal(paramName)
		myTable = MyCustomTable(numDecimal)
		myTable.addData('Original', tscm.getData())
		table = myTable.getTable()
		self.tableTopPane.add(JScrollPane(table)) 

		missingPane = JPanel()
		missingPane.setBorder( BorderFactory.createTitledBorder("Missing") )
		missingTextField = JTextField(8)
		missingTextField.setText(orgDataTable.getStringMissing())
		missingPane.add(missingTextField)

		rejectedPane = JPanel()
		rejectedPane.setBorder( BorderFactory.createTitledBorder("Rejected") )
		rejectedTextField = JTextField(8)
		rejectedTextField.setText(orgDataTable.getStringRejected())
		rejectedPane.add(rejectedTextField)

		replacePane = JPanel()
		replacePane.setBorder( BorderFactory.createTitledBorder("Replaced") )
		replaceTextField = JTextField(8)
		replaceTextField.setText(orgDataTable.getStringReplaced())
		replacePane.add(replaceTextField)
		
		tableMidPane = JPanel()#JSplitPane(JSplitPane.HORIZONTAL_SPLIT,self.stationsTree, self.stationInfoPane)
		tableMidPane.setLayout(BoxLayout(tableMidPane, BoxLayout.LINE_AXIS))
		tableMidPane.add(missingPane)
		tableMidPane.add(rejectedPane)
		tableMidPane.add(replacePane)

		tableBottomPane = JPanel()
		tableBottomPane.setLayout(BoxLayout(tableBottomPane, BoxLayout.LINE_AXIS))
		tableBottomPane.add(JButton('Reset', actionPerformed=self.onReset))
		tableBottomPane.add(JButton('Plot', actionPerformed=self.onPlotParam))
		plotComboBox = JComboBox(['parameter','station'])
		tableBottomPane.add(plotComboBox)
		tableBottomPane.add(JButton("Save As Copy", actionPerformed=self.onSaveCopy))
		tableBottomPane.add(JButton("Overwrite", actionPerformed=self.onOverwrite))
	
		tablePane.add( self.tableTopPane )
		tablePane.add(tableMidPane)
		tablePane.add( tableBottomPane)
		parentPane.add(tablePane)
		self.stationDict[stationName][paramName]['reportTextField'] = [missingTextField, rejectedTextField, replaceTextField] 
		self.stationDict[stationName][paramName]['plotComboBox'] = plotComboBox 
		self.stationDict[stationName][paramName]['myTable'] = myTable 
		
	#This funtion generates the GUI of the reporting data at the bottom of the dashboard.
	def updateReportTextField(self, stationName, paramName):
		missingTextField, rejectedTextField, replaceTextField = self.stationDict[stationName][paramName]['reportTextField']  
		orgDataTable = self.stationDict[stationName][paramName]['orgDataTable'] 
		missingTextField.setText(orgDataTable.getStringMissing())
		rejectedTextField.setText(orgDataTable.getStringRejected())
		replaceTextField.setText(orgDataTable.getStringReplaced())
	
	#This function handles the event of user choose to reset the dataset - i.e clear to performed taskes.
	def onReset(self,event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent() #plotButton->tableBottomPane->tablePane->stationTopPane->StationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent() 
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)

		self.stationDict[stationName][paramName]['computeReplaceButton' ].setEnabled(True)
		self.stationDict[stationName][paramName]['computeScreenButton' ].setEnabled(True)

		numDecimal = self.getNumDecimal(paramName)
		myTable = MyCustomTable(numDecimal)
		tscm = self.stationDict[stationName][paramName]['orgDataTable'].getMergedTscm()
		myTable.addData('Original', tscm.getData())
		table = myTable.getTable()
		self.tableTopPane.removeAll()
		self.tableTopPane.add(JScrollPane(table)) 
		self.tableTopPane.revalidate()

		self.stationDict[stationName][paramName]['myTable'] = myTable
		self.stationDict[stationName][paramName]['orgDataTable'].resetDataTable()
		self.updateReportTextField(stationName, paramName)
		remove_Tscm = self.stationDict[stationName][paramName].pop("modifiledTscm", None)

	#This function handles the event where the user clicks on Overwrite Button
	def onOverwrite(self, event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent() #plotButton->tableBottomPane->tablePane->stationTopPane->StationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent() 
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		
		orgDataTable = self.stationDict[stationName][paramName]['orgDataTable']
		orgDataTable.overwrite()
		self.repaintPanel(stationName, paramName,'overwrite')
	
	#This function handles the event where the user clicks on "Save as copy" Button
	def onSaveCopy(self, event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent() #plotButton->tableBottomPane->tablePane->stationTopPane->StationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent() 
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		print('onSaveCopy')
		orgDataTable = self.stationDict[stationName][paramName]['orgDataTable']
		stationName, paramName = orgDataTable.saveCopy()
		self.repaintPanel(stationName, paramName,'copy')
	
	#This function repaints the station JTree as new pathname is added
	def repaintPanel(self, stationName, paramName, mode):
		self.stationDict = updateStationDict(self.fileName, self.stationDict, stationName, paramName)
		self.stationsTree = self.updateTree(stationName, paramName,mode)
		self.mainFrame.repaint()
		
	#This function handles the event where the user clicks on Plot Button
	def onPlotParam(self, event): 
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent() #plotButton->tableBottomPane->tablePane->stationTopPane->StationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent() 
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)

		#  Initialize the plot and add data
		plot = Plot.newPlot(paramName+' - '+stationName)
		tscToPlot = self.stationDict[stationName][paramName]['orgDataTable'].getMergedTscm().getData()
		if self.stationDict[stationName][paramName].has_key('modifiledTscm'):
			tscToPlot, _ = self.stationDict[stationName][paramName]['orgDataTable'].removeRejected()
			tscToPlot = tscToPlot.getData()
		plot.addData(tscToPlot)

		selectedPlot = self.stationDict[stationName][paramName]['plotComboBox'].selectedIndex
		if selectedPlot==1: #plot station
			for param in self.stationDict[stationName]['paramNameList']:
				tsc = self.stationDict[stationName][param]['orgDataTable'].getMergedTscm().getData()
				print(tsc.fullName)
				plot.addData(tsc)
	        
		plot.setSize(600,600)
		plot.setLocation(100,100)
		plot.showPlot()
		
	'''
	This class helps defined the GUI of the spinner input - bold with grey background as it is back to the default value.
	'''
	class BoldListener(ChangeListener):
		def __init__(self, spinner, defaultValue):
			self.spinner = spinner
			self.defaultValue = defaultValue
			super(ChangeListener, self).__init__()
		def stateChanged(self, event):
			currentValue = event.getSource().getValue()
			if currentValue == self.defaultValue:
				self.spinner.getEditor().getTextField().setBackground(defaultBackgroundSpinner_CONST)
			else:
				self.spinner.getEditor().getTextField().setBackground(Color.WHITE)
	
	#This functions collects the user's choice of Change Limit
	def onTypeChangeLimit(self,event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent()  #ComputeButton->ScreenPane->stationPane->stationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent()
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		_, _, _,  percentageButton, absDiffButton, _ = self.stationDict[stationName][paramName]['screenCheckboxComponent'] 
		if percentageButton.isSelected():
			self.stationDict[stationName][paramName]['typeChangeLimit'] = 'percentage'
		elif absDiffButton.isSelected():
			self.stationDict[stationName][paramName]['typeChangeLimit'] = 'absDiff'
		
	#This functions generates the GUI for the screening conditions
	def addScreenConditions(self, screenTopPanel, c,  cond_label, defaultValue, row, displayUnits, endOrdinate_DEFAULT=None):
		col_start = 2
		c.gridx, c.gridy, c.ipady= col_start, row, 6
		screenTopPanel.add( JLabel('       '+ cond_label+': ' ),c )

		col_start+=1
		checkbox = JCheckBox('', actionPerformed = self.onCheckBoxConditions)
		c.gridx, c.gridy, c.ipady= col_start, row, 6
		checkbox.setSelected(True)
		screenTopPanel.add(checkbox, c)
		
		if cond_label == 'Moving average over':
			model = SpinnerNumberModel(1,1 , endOrdinate_DEFAULT, 1)
		else:
			model = SpinnerNumberModel(defaultValue,minValue_CONST , maxValue_CONST, stepValue_CONST)
		spinner = JSpinner(model)
		spinner.getEditor().getTextField().setBackground(defaultBackgroundSpinner_CONST)
		spinner.getModel().addChangeListener(self.BoldListener(spinner, defaultValue))

		col_start +=1
		c.gridx, c.gridy, c.ipady= col_start, row, 6
		screenTopPanel.add( spinner,c)

		col_start +=1
		c.gridx, c.gridy, c.ipady= col_start, row, 6
		if cond_label != 'Change Limit':
			screenTopPanel.add( JLabel('  '+ displayUnits ),c )
		else:
			c.gridx, c.gridy, c.ipady= col_start, row, 6
			absDiffButton = JRadioButton("Abs Difference", actionPerformed=self.onTypeChangeLimit)
			screenTopPanel.add( absDiffButton, c )
			absDiffButton.setSelected(True)
			col_start +=1
			c.gridx, c.gridy, c.ipady= col_start, row, 6
			percentageButton = JRadioButton("%", actionPerformed=self.onTypeChangeLimit)
			screenTopPanel.add( percentageButton, c )
			changeLimitTypeGroup = ButtonGroup()
			changeLimitTypeGroup.add(absDiffButton)
			changeLimitTypeGroup.add(percentageButton)
			return spinner, checkbox, absDiffButton, percentageButton
			
		return spinner, checkbox
	
	#This function generates the GUI for the screening tab sections
	def addScreenTab(self, parentTabbedPane, stationName, paramName):
		screenPane = JPanel()
		screenPane.setLayout(BoxLayout(screenPane, BoxLayout.Y_AXIS))

		screenTopPanel = JPanel()
		screenTopPanel.setLayout( GridBagLayout() )
		c = GridBagConstraints()
		screenTopPanel.setBorder( BorderFactory.createTitledBorder(paramName) )

		minDefaultValue, maxDefaultValue, changeDefaultValue, displayUnits = getDefaultScreenValue(paramName.split('/')[0])
		c.anchor =  GridBagConstraints.WEST 
		#add time window option
		startOrdinate_DEFAULT= 1
		endOrdinate_DEFAULT = self.stationDict[stationName][paramName]['numValues']
		c.gridx, c.gridy= 0, 0 #x,y
		ordinate_label = JLabel("<html><b>Ordinate</b>")
		screenTopPanel.add(ordinate_label, c)
		c.gridx, c.gridy= 0, 1 #x,y
		start_time_label =  JLabel("<html>Start")
		screenTopPanel.add(start_time_label, c)
		c.gridx, c.gridy= 1, 1 #x,y
		start_time_model = SpinnerNumberModel(startOrdinate_DEFAULT,startOrdinate_DEFAULT ,endOrdinate_DEFAULT,1) #default value as 0 ordinate
		start_time_spinner = JSpinner(start_time_model)
		screenTopPanel.add(start_time_spinner, c)
		c.gridx, c.gridy= 0, 2 #x,y
		end_time_label = JLabel("<html>End")
		screenTopPanel.add(end_time_label, c)
		c.gridx, c.gridy= 1, 2 #x,y
		end_time_model = SpinnerNumberModel(endOrdinate_DEFAULT,startOrdinate_DEFAULT,endOrdinate_DEFAULT,1) #default value as end ordinate
		end_time_spinner = JSpinner(end_time_model)
		screenTopPanel.add(end_time_spinner, c)
		self.stationDict[stationName][paramName]['timeWindowScreenSpinner'] = [start_time_spinner, end_time_spinner]

		c.gridx, c.gridy= 2, 0 #x,y
		conditions_label = JLabel("<html> <b>Conditions</b>")
		screenTopPanel.add(conditions_label, c)

		min_spinner, min_checkbox = self.addScreenConditions(screenTopPanel, c,  'Min Value', minDefaultValue, 1,displayUnits)
		max_spinner, max_checkbox = self.addScreenConditions(screenTopPanel, c,  'Max Value',maxDefaultValue,  2,displayUnits)
		change_spinner, change_checkbox , absDiffButton, percentageButton= self.addScreenConditions(screenTopPanel, c,  'Change Limit',changeDefaultValue,  3,'%')
		points_spinner, points_checkbox = self.addScreenConditions(screenTopPanel, c,  'Moving average over',changeDefaultValue,  4, 'point(s)',endOrdinate_DEFAULT)

		self.stationDict[stationName][paramName]['screenSpinnerComponent'] = [min_spinner, max_spinner, change_spinner, points_spinner]
		self.stationDict[stationName][paramName]['screenCheckboxComponent'] = [min_checkbox, max_checkbox, change_checkbox,  percentageButton, absDiffButton, points_checkbox]
		self.stationDict[stationName][paramName]['typeChangeLimit'] = 'absDiff'
		self.stationDict[stationName][paramName]['checkBoxStatus'] = [True, True, True, True]
		
		screenPane.add( screenTopPanel)
		screenPane.add( JLabel('\nInvalid value will be marked as R (rejected)', alignmentX = Component.CENTER_ALIGNMENT ))
		computeScreenButton = JButton("Compute", alignmentX = Component.CENTER_ALIGNMENT, actionPerformed=self.onComputeScreen)
		self.stationDict[stationName][paramName]['computeScreenButton' ] = computeScreenButton
		screenPane.add(computeScreenButton)
		parentTabbedPane.addTab('Screen', screenPane)
		
	#This functions allows activate/ deactivate of the screening conditions.
	def onoffScreenCondtions(self, checkbox, const, default,  spinner, mode):
		if mode=='deactivate':
			spinner.setValue(const)
			spinner.getEditor().getTextField().setBackground(deactivateBackgroundSpinner_CONST)
			spinner.getEditor().getTextField().setEditable(False)
		elif mode=='activate':
			spinner.setValue(default)
			spinner.getEditor().getTextField().setEditable(True)

	#This functions handles the events of user checking the screening conditions box
	def onCheckBoxConditions(self, event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent().getParent()  #ComputeButton->ScreenPane->stationPane->stationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent().getParent()
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		param, cPart,  time, fPart = getColumnFromBranchName(paramName)
		min_checkbox, max_checkbox, change_checkbox, _, _, points_checkbox = self.stationDict[stationName][paramName]['screenCheckboxComponent'] 
		min_spinner, max_spinner, change_spinner, points_spinner = self.stationDict[stationName][paramName]['screenSpinnerComponent'] 
		min_status, max_status, change_status, points_status = self.stationDict[stationName][paramName]['checkBoxStatus']
		minDefaultValue, maxDefaultValue, changeDefaultValue, displayUnits = getDefaultScreenValue(paramName.split('/')[0])
		pointsDefaultValue = 1

		if min_checkbox.isSelected() == min_status: #no change
			pass
		else: #
			min_mode = 'activate' if min_checkbox.isSelected() else 'deactivate'
			self.onoffScreenCondtions(min_checkbox, minValue_CONST, minDefaultValue,  min_spinner, min_mode)
			self.stationDict[stationName][paramName]['checkBoxStatus'][0] = not min_status

		if max_checkbox.isSelected() == max_status: #no change
			pass
		else: #
			max_mode = 'activate' if max_checkbox.isSelected() else 'deactivate'
			self.onoffScreenCondtions(max_checkbox, maxValue_CONST,maxDefaultValue,  max_spinner, max_mode)
			self.stationDict[stationName][paramName]['checkBoxStatus'][1] = not max_status

		if change_checkbox.isSelected() == change_status: #no change
			pass
		else: #
			change_mode = 'activate' if change_checkbox.isSelected()  else 'deactivate'
			self.onoffScreenCondtions(change_checkbox, maxValue_CONST, changeDefaultValue , change_spinner ,  change_mode)
			self.stationDict[stationName][paramName]['checkBoxStatus'][2] = not change_status
			
		if points_checkbox.isSelected() == points_status: #no change
			pass
		else: #
			points_mode = 'activate' if points_checkbox.isSelected()  else 'deactivate'
			self.onoffScreenCondtions(points_checkbox, pointsDefaultValue , pointsDefaultValue, points_spinner,  points_mode)
			self.stationDict[stationName][paramName]['checkBoxStatus'][2] = not points_status

	#This function helps to display the original data column in the data table
	def displayOriginalColumn(self, myTable, column):
		myTable.setColumnLabel(column, 'Original')
		return myTable
		
	#This function helps to customize the display of a column in the data table
	def displayColumn(self, myTable, columnName, column,  modifiedIndex, color):
		myTable.setColumnLabel(column,columnName)
		myTable.getTable().setEditable(False)
		for index in modifiedIndex:
			myTable.getTable().setCellBackground(index+2,column,color)
		return myTable
	def getTypeChangeLimit(self, paramName, stationName):
		return self.stationDict[stationName][paramName]['typeChangeLimit']
	
	#This function handles the events of user clicking the Compute button for the screening task.
	def onComputeScreen(self, event):
		stationInfoPane = event.getSource().getParent().getParent().getParent().getParent()  #ComputeButton->ScreenPane->stationPane->stationInfoPane
		stationPane = event.getSource().getParent().getParent().getParent()
		stationName, paramName = getStationParamName(stationInfoPane, stationPane)
		param, cPart,  time, fPart = getColumnFromBranchName(paramName)

		self.stationDict[stationName][paramName]['computeScreenButton' ].setEnabled(False)

		timeIdx_obj = TimeIdx(self.stationDict[stationName][paramName]['timeWindowScreenSpinner'])
		timeIdx = timeIdx_obj.getTimeIdx()
		
		minValue, maxValue, changeLimit, pointsSpan = self.getScreenSpinnerValue(stationName, paramName)
		typeChangeLimit = self.getTypeChangeLimit(paramName, stationName)
		orgTscm = self.stationDict[stationName][paramName]['orgDataTable']
		screenTscm, rejectedIndex = orgTscm.screenTscm(minValue, maxValue, changeLimit, timeIdx, pointsSpan,  typeChangeLimit)

		self.stationDict[stationName][paramName]['rejectedIndex'] = rejectedIndex
		self.stationDict[stationName][paramName]['modifiledTscm'] = screenTscm
		
		myTable = self.stationDict[stationName][paramName]['myTable']
		myTable.addData('Screen', screenTscm.getData(), rejectedCell=rejectedIndex)

		print('column count', myTable.getTable().getColumnCount() )

		self.stationDict[stationName][paramName]['myTable'] = myTable
		self.updateReportTextField(stationName, paramName)
		
	#This function gets the spinner values for user input
	def getScreenSpinnerValue(self, stationName, paramName):
		min_spinner, max_spinner, change_spinner, points_spinner = self.stationDict[stationName][paramName]['screenSpinnerComponent']
		return min_spinner.getValue(), max_spinner.getValue(), change_spinner.getValue(), points_spinner.getValue()

	#This function gets the spinner values (ordinate only) for user input
	def getTimeWindowSpinnerValue(self, stationName, paramName, mode): #mode is 'replace' or 'screen'
		if mode=='replace':
			whichspinner = 'timeWindowReplaceSpinner'
		else: #mode=='screen'
			whichspinner = 'timeWindowScreenSpinner'
		start_spinner, end_spinner = self.stationDict[stationName][paramName][whichspinner]
		return start_spinner.getValue(), end_spinner.getValue()
		
	# LET'S RUN THE PROGRAM
	def run(self):
		self.mainFrame.setVisible(1)

'''
HELPER FUNCTIONS
'''

'''
MAIN FUNCTION
'''
def main():
	if not ListSelection.isInteractive():
	    print("The script must be run inside HEC-DSSVue") #error
	else: 
		mainWindow = ListSelection.getMainWindow() #get the currenlty open .dss file
		windowTime =[mainWindow.getStartTime(), mainWindow.getEndTime()] #get the time window if specified
		if not hasTimeWindow(windowTime):
			print("No time window selected")

		dssFilename = mainWindow.getDSSFilename() #open .dss file
		if dssFilename is None:
			messageDialog('No opened data file')
		mainFrame = MainFrame_revised(dssFilename, windowTime) #initialize the dashboard
		mainFrame.run() #run the dashboard.


if __name__=='__main__':
	main()
