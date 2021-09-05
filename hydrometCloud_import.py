# name=hydrometCloud_import
# description=all station worked accept for fremont
# description=change param name
# displayinmenu=true
# displaytouser=true
# displayinselector=true
from hec.script import Tabulate
from hec.script import Plot, AxisMarker
from hec.heclib.dss import HecDss, DSSPathname
from javax.swing import *
import java
import struct
from javax.swing import *
#from javax.swing import JTree
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
from copy import deepcopy

from hec.heclib.dss import HecDss, HecTimeSeries
from hec.io import TimeSeriesContainer
from hec.heclib.util import HecTime

from hec.script import *
from hec.heclib.dss import *
import java
from hec.heclib.dss import HecDss, HecTimeSeries
from hec.io import TimeSeriesContainer, DataContainer
from hec.heclib.util import HecTime
import glob

#values_dict = {} 
#times_dict = {} 
num_to_month = {'1':'Jan', '2':'Feb', '3':'Mar', '4':'Apr','5':'May','6':'Jun','7':'Jul','8':'Aug','9':'Sep','10':'Oct','11':'Nov','12':'Dec'}
fileName_to_stationName = {
#'agatha_canal':'AGATHA CANAL',
#'camp_13': 'CAMP 13', 
'fremont@GCR':'Fremont @ GCR',
#'sfc_upstream':'SFC Upstream',
#'sfc_downstream':'SFC Downstream',
#'sfc_discharge':'SFC Discharge',
#'cherokee_ditch': 'Cherokee Ditch',
#'eagle_ditch':'Eagle Ditch',
#'hollow_tree_pump_station':'HOLLOW TREE PUMP STATION',
#'gun_club_pump_station':'Gun Club Pump Station',
'hollow_tree':'HOLLOW TREE',
#'lone_tree':'LONE TREE',
'LBCreek@140':'LB Creek @ 140',
'mudslough@GCR':'Mudslough @ GCR',
#'robin_nest':'Robin\'s Nest',
#'robin_nest':'Robins Nest',
#'robins_nest':'Robins Nest',
#'sfc@152':'SFC @ 152',
#'sfc@skeleton':'SFC @ Skeleton',
#'sl1':'SL 1',
's_lake':'S-Lake',
's_lake_no_dash':'S-Lake'} 
#'s_lake_no_dash':'S Lake',
#'slc@bgu':'SLC @ BGU',
#'slc@bgu':'SLC @ Blue Goose Unit',
#'slc@bluegooseunit':'SLC @ Blue Goose Unit',
#'slc_pre_splits':'SLC Pre Splits',
#'westside_ditch':'Westside Ditch',
#'volta_upstream':'Volta Upstream',
#'volta_wasteway':'Volta Wasteway',
#'x_channel':'X-Channel'

missingNumericValue_CONST = -3.4028234663852886e+38 

#CHANGE THIS to the file path of your .dss file
fileName = 'C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/hydrometCloud/hydromet_ver1.dss' # 'C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/my_scripts/gwd/gwd_ver5.dss' #"C:/Users/vitran/Documents/gwd_data/gwd_ver7.dss"
dssFile = HecDss.open(fileName)



input_path ='C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/hydrometCloud/new_download/csv/'# 'C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/my_scripts/gwd/data/'# 'C:/Users/vitran/Documents/gwd_data/csv_2018_2019/'
inputFiles = glob.glob(input_path+'*.csv')
print(inputFiles)

try:
	for csv_name in inputFiles:
		stationFileName =  csv_name.strip().split('/')[-1].split('\\')[-1][:-4]
		if stationFileName in fileName_to_stationName.keys():
			stationName = fileName_to_stationName[csv_name.strip().split('/')[-1].split('\\')[-1][:-4]]
			print(stationName)
			reader=  open(csv_name,'r') 
			row0 = next(reader)
			params = row0.strip().split(',')
		
			print(params)
			row1 = next(reader)
			units = row1.strip().split(',')
#			units = units[1:]
			print(units)
			hectime = HecTime()
			cont_values_list = {}
			times = []
			quality_list= {}
			qa_index = []
			qa_name_dict = {}
			qa_times_dict = {}
			qa_values_dict = {}
			notes = []
#			note_index = 99999
			
			empty_param = len(params)+1
			for i in range(len(params)):
				if i!=0:
					param = params[i]
					if len(param) >0 : #and 'QA' not in param
						if 'QA' in param:
							qa_index.append(i)
							qa_times_dict[i] = []
							qa_values_dict[i] = []
							qa_name_dict[i] = param
#							print('add to qa_name_dict', param)
						else: 
#							print('add to cont_value_list', param)
							cont_values_list[i] = []
							quality_list[i] = []
					else: 
	#					note_index = i+1
						empty_param = i+2 #add 2 for 2019 only  as Notes column #1 for 2018
#						print(empty_param, note_index)
						break
			params = params[:empty_param]
#			print(qa_index)
#			print(len(cont_values_list))
	#		try:
			for row in reader:
				row = row.strip().split(',')
				if row[0] != '':
					date = row[0].strip().split('/')
#					print(empty_param)
#					print('row', len(row), row)
					dateString = date[1]+num_to_month[date[0]]+date[2]
					date_inp, time_inp = row[0].strip().split(' ')
					
					date_str = date_inp.strip().split('/')
					dateString = date_str[1]+num_to_month[date_str[0]]+date_str[2]

					datetimeString = dateString + ' ' + time_inp + ':00'
					
					hectime.set(datetimeString)
#					print(datetimeString)
					
					if len(times)>0 and  hectime.value()-times[-1] != 15:
						num_missing =  (hectime.value()-times[-1])//15 - 1
						print('missing x days ', num_missing)
						for day in range(num_missing):
							times.append(times[-1]+1440)
							for i in range(len(row[:empty_param])):
								if i==0:
									continue
								if i not in qa_index:
									quality_list[i].append(5) #missing
									cont_values_list[i].append(missingNumericValue_CONST)
#					print(row[:empty_param])
					times.append(hectime.value())
					for i, value_str in enumerate(row[:empty_param]):
		#					print(i,empty_param,  empty_param)
						if i==0:
							continue
#						elif i==note_index:
#							notes.append(value_str) #this is QA notes
#						else:
#						print('he', i)
						if i not in qa_index:
							if len(value_str) >0:
								cont_values_list[i].append(float(value_str))
								quality_list[i].append(1)
							else:
								quality_list[i].append(5) #missing
								cont_values_list[i].append(missingNumericValue_CONST)
						else:
#								print('add to qa dict', i, value_str)
							if len(value_str)>0:
								qa_times_dict[i].append(hectime.value())
								qa_values_dict[i].append(float(value_str))
	#		except:
	#			print('exception here')
			
			reader.close()
			print('AFTER CLOSE CSV')
			for i, values in cont_values_list.items():
				flag = 0
				test_list1 = times
				test_list1.sort()
				if (test_list1 == times):
				   	flag = 1

#					print('saving' , params[i].upper(), stationName.upper())
					tsc = TimeSeriesContainer()
					print(params[i])
					tsc.watershed = ''
					tsc.location = stationName.upper()
					tsc.parameter = params[i].upper()
					tsc.fullName = "/%s/%s/%s//15MIN/%s/" % (tsc.watershed, tsc.location, tsc.parameter,'OBSERVED')
					
					tsc.interval =  15
					
					tsc.values = values
					tsc.times = times
					tsc.startTime =times[0]
					tsc.endTime = times[-1]
					
					tsc.numberValues = len(values)
#					print('before quality', len(values), len( quality_list[i]))
					tsc.quality = quality_list[i]
					print('after quality')
					mess =  'times vs values' + str( len(times)) + '----'+str(len(values)) + '\n' + str( times ) + '\n' + str(values )
					assert len(times)==len(values) , mess
					assert  len(times)==len(tsc.quality), 'times vs quality'
					print(i, units)
					tsc.units = units[i]
					tsc.type = 'INST-VAL'
#					print('before put')
					dssFile.put(tsc)
					startTime = HecTime()
					startTime.set(tsc.startTime)
					endTime = HecTime()
					endTime.set(tsc.endTime)
#					print('time ', startTime.toString(), endTime.toString())
					print('add  ', tsc.fullName, 'numberValues ', tsc.numberValues )
				else:
					print('cont time not sort')
					k=1
					while k<len(times):
						if times[k-1] >= times[k]:
	
							hectime = HecTime()
							hectime.set(times[k])
	
							hectime_n = HecTime()
							hectime_n.set(times[k-1])
							print('DIFFERENCE')
							print(hectime.toString(), hectime_n.toString())
						k+=1

			for index in qa_index:
				# using sort() to 
				# check sorted list 
				flag = 0
				test_list1 = qa_times_dict[index][:]
				test_list1.sort()
				if (test_list1 == qa_times_dict[index]):
				   	flag = 1
								
					tsc = TimeSeriesContainer()
					tsc.watershed = ''
					tsc.location = stationName.upper()
					tsc.parameter = qa_name_dict[index].upper()
					tsc.fullName = "/%s/%s/%s//IR-MONTH/%s/" % (tsc.watershed, tsc.location, tsc.parameter,'QA')
					
					tsc.values = qa_values_dict[index]
#					tsc.setCharacterNotes (notes)
	#				print(tsc.getCharacterNotes())
					tsc.times =  qa_times_dict[index]
#					print(index)
#					print(tsc.times)
#					print(tsc.values)
					assert len( qa_values_dict[index]) == len(qa_times_dict[index]),'values and times not match'+  len( qa_values_dict[index]) +' - '+  len( qa_times_dict[index])
					
					tsc.numberValues = len(tsc.values)
					tsc.quality = [1 for j in range(len(tsc.values))]
					tsc.units = units[index]
#					print('units', tsc.units)
					tsc.type = 'INST-VAL'
					dssFile.put(tsc)
#					print('add  ', tsc.fullName, 'numberValues ', tsc.numberValues )
				else:
					print('qa time not sort')
					k=1
					while k<len(qa_times_dict[index]):
						if qa_times_dict[index][k-1] >= qa_times_dict[index][k]:
	
							hectime = HecTime()
							hectime.set(qa_times_dict[index][k])
	
							hectime_n = HecTime()
							hectime_n.set(qa_times_dict[index][k-1])
							print('DIFFERENCE')
							print(hectime.toString(), hectime_n.toString())
						k+=1
					
except :
	print('exception')
#path_names = dssFile.getPathnameList()
#for n in path_names:
#    print(n)
dssFile.done()
