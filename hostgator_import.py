# name=hostgator_import
# description=data import from hostgator server
# description=correct format
# description=FINAL
# description=Aug 15: switch param name to follow mercury's naming convention (param A as param name)
# displayinmenu=true
# displaytouser=true
# displayinselector=true
from hec.script import *
from hec.heclib.dss import *
import java
from hec.heclib.dss import HecDss, HecTimeSeries
from hec.io import TimeSeriesContainer
from hec.heclib.util import HecTime
import glob


#num_to_month = {'01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
num_to_month = {'1':'Jan', '2':'Feb', '3':'Mar', '4':'Apr','5':'May','6':'Jun','7':'Jul','8':'Aug','9':'Sep','10':'Oct','11':'Nov','12':'Dec','01':'Jan', '02':'Feb', '03':'Mar', '04':'Apr','05':'May','06':'Jun','07':'Jul','08':'Aug','09':'Sep'}
units_dict = {'stage':'ft', 'emp':'F', 'Volts':'V','EC':'uS/cm', 'stage':'ft'}
missingNumericValue_CONST = -3.4028234663852886e+38 
#CHANGE THIS to the folder that stores the raw input file
input_path ='C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/hosgator_import/' #'C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/test_import/'#'C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/'
input_path ='C:/Users/trnng/Documents/OCC/Internship/cci/hostgator/hostgator_Aug15/'
print('restart')
#CHANGE THIS to the your station name 
#station=  'MARSHALL'#'INGRAM CREEK'
#station=  'INGRAM CREEK'

#CHANGE THIS to the file path of your .dss file
dssFile = HecDss.open("C:/Users/trnng/Documents/OCC/Internship/cci/hecdssvue/hosgator_import/hosgator_import_Aug15.dss")




inputFiles = glob.glob(input_path+'*.csv')

for file_name in inputFiles:
	station=  file_name.split('/')[-1].split('\\')[-1].split('_')[0].upper()
	print(file_name)
	print(station)
	values_dict = {} 
	times_dict = {} 
	quality_dict = {} 
	
	txtfile = open(file_name,'r')
	for line in txtfile:
		if line !='\n':
	    		line= line.strip().split(',')
    			if len(line)>1:
			        date_lst = line[0].strip().split('/')
			        time_lst = line[1].strip().split(':')
			        param = line[2]
			        val = line[3]
			        try:
			            val = float(val)
			        except Exception :
			            pass
			            # print ('invalid entry ', line, ' from file ', file_name)

		if isinstance(val,float) and val>=0.0:
#			print(date_lst)
			date_str = date_lst[1]+num_to_month[date_lst[0]]+date_lst[2]
			time_str = time_lst[0]+time_lst[1]
			hecTime = HecTime()
			hecTime.set(date_str+' '+time_str)
			
			if param in times_dict:
				interval = hecTime.value()-times_dict[param][-1]
				if interval >15:
					num_interval =( interval // 15) 
			
					hecStart = HecTime()
					hecStart.set(times_dict[param][-1])
			
					hecNext = HecTime()
					hecNext.set(hecTime.value())
#					print('missing ', num_interval, hecStart.toString(), hecNext.toString())
					for n in range(num_interval):
						values_dict[param].append(missingNumericValue_CONST)
						times_dict[param].append(times_dict[param][-1]+15)
						quality_dict[param].append(5)
				elif interval !=0:
					times_dict[param].append(hecTime.value())
					values_dict[param].append(val)
					quality_dict[param].append(1)
				else:
					print('duplicate at ', hecTime.toString())
			else:
				times_dict[param] = [hecTime.value()]
				values_dict[param] = [val]
				quality_dict[param] = [1]
	txtfile.close()

	all_params = values_dict.keys()
	print(all_params)
	
	for param in all_params:
		tsc = TimeSeriesContainer()
		tsc.watershed = param.upper()[3:]
		tsc.location = station
		
		tsc.parameter = ''
		tsc.fullName = "/%s/%s/%s//15MIN//" % (tsc.watershed, tsc.location, tsc.parameter)
		print(tsc.fullName)
		tsc.interval = 15
		
		tsc.values = values_dict[param]
		tsc.times = times_dict[param]
		tsc.quality = quality_dict[param] 
		assert len(tsc.values) == len(tsc.times),'values and times not match'+ ' values  ' + str(len(tsc.values))+ ' times  ' + str(len(tsc.times))+ ' quality  ' + str(len(tsc.quality))
		tsc.startTime = times_dict[param][0]
		tsc.endTime = times_dict[param][-1]
		
		tsc.numberValues = len(values_dict[param])
		
		for key, value in units_dict.items(): 
			if key in param[3:]:
			    	tsc.units = value
			#            print(tsc.units)
		    		break
		tsc.type = 'INST-VAL'
		print(tsc.fullName)
		#    print(tsc.times)
		#    print(tsc.values)
		dssFile.put(tsc)

#path_names = dssFile.getPathnameList()
#for n in path_names:
#    print(n)
dssFile.close()

