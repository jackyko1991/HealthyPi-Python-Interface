import serial
import time
import csv
import matplotlib
matplotlib.use("tkAgg")
import matplotlib.pyplot as plt
import numpy as np
import struct
import time
import threading
from collections import deque
import datetime
import signal
import sys
import argparse
import os

COM_PORT = 'COM3'
BAUD_RATES = 57600
PLOT = True # plot slow down the program to around 12FPS and causes signal blocking

def reversePacket(dataPacket,n):
	if n == 0:
		return dataPacket[n]<<(n*8)
	else:
		return (dataPacket[n]<<(n*8))| reversePacket(dataPacket, n-1)

# fast plotting https://gist.github.com/electronut/d5e5f68c610821e311b0

class HealthyPiCollector(threading.Thread):
	"""
		The HealthyPi class will spawn a sparate thread to avoid main thread blocking during data collection
	"""
	def __init__(self,data,port,lock,event,baud_rate=57600):
		super(HealthyPiCollector, self).__init__()
		self.data=data
		self.port=port
		self.lock=lock
		self.event=event
		self.baud_rate=baud_rate
		self.serial = None

	def open(self):
		# open serial port on thread startup
		self.serial = serial.Serial(self.port,self.baud_rate)
		self.serial.flushInput()

	def close(self):
		# close serial port
		self.serial.flush()
		self.serial.close()

	def run(self):
		print("Data collection start, press CTRL+C to stop")
		while self.event.is_set():
			raw_data = self.serial.readline()
			print(self.event.is_set(),raw_data)

def main(args):
	if args.csv:
		# create folder for data export
		if not os.path.exists(args.ouptut_folder):
			os.makedirs(args.ouptut_folder)

		# create csv files
		dt = datetime.datetime.now()
		datetime_str = dt.strftime("%Y%m%d-%H%M%S")
		signalsCsv = open(args.ouptut_folder + "/"+ args.prefix + "_" + datetime_str + "_Signals.csv",'w')
		numericsCsv = open(args.ouptut_folder + "/"+ args.prefix + "_" + datetime_str + "_Numerics.csv",'w')



	data = deque([])
	lock = threading.Lock()

	running_event = threading.Event()
	running_event.set()

	collector = HealthyPiCollector(data,args.port,lock,running_event,BAUD_RATES)
	collector.open()
	collector.start()

	while True:
		try:
			print("hello")
			# collector.join(0.1)
		except KeyboardInterrupt:
			print("Stopping data collection, wait till serial port close...")
			running_event.clear()
			collector.join()
			collector.close()
			print("Stopped data collection")
			sys.exit()

	# if PLOT:
	# 	y_var = np.array(np.zeros([plot_window]))
	# 	plt.ion()
	# 	fig, ax = plt.subplots()
	# 	line, = ax.plot(y_var)

	# ecg = []
	# ir = []
	# red = []

	# while True:
	# 	start_time = time.time()
	# 	data_raw = ser.readline()

	# 	if not len(data_raw) == 27:
	# 		continue
		
	# 	ECG = int.from_bytes(data_raw[4:6], byteorder='big',signed=True)
	# 	resp_val = int.from_bytes(data_raw[6:8], byteorder='big',signed=True)
		
	# 	# PPG
	# 	ppg_ir_val_ = []
	# 	ppg_ir_val_.append(int.from_bytes(data_raw[8:9], byteorder='big',signed=False))
	# 	ppg_ir_val_.append(int.from_bytes(data_raw[9:10], byteorder='big',signed=False))
	# 	ppg_ir_val_.append(int.from_bytes(data_raw[10:11], byteorder='big',signed=False))
	# 	ppg_ir_val_.append(int.from_bytes(data_raw[11:12], byteorder='big',signed=False))
	# 	ppg_ir_val = reversePacket(ppg_ir_val_,len(ppg_ir_val_)-1)

	# 	ir.append(ppg_ir_val)
	# 	if len(ir) < plot_window:
	# 		pass
	# 	else:
	# 		ir = ir[1:plot_window+1]
	# 	irAvg = np.mean(ir)
	# 	ppg_ir_val = (ir[len(ir)-1]-irAvg)
	# 	# if ppg_ir_val < 0:
	# 	# 	ppg_ir_val = 0
	# 	# else:
	# 	# 	ppg_ir_val = ppg_ir_val

	# 	ppg_red_val_ = []
	# 	ppg_red_val_.append(int.from_bytes(data_raw[12:13], byteorder='big',signed=False))
	# 	ppg_red_val_.append(int.from_bytes(data_raw[13:14], byteorder='big',signed=False))
	# 	ppg_red_val_.append(int.from_bytes(data_raw[14:15], byteorder='big',signed=False))
	# 	ppg_red_val_.append(int.from_bytes(data_raw[15:16], byteorder='big',signed=False))
	# 	ppg_red_val = reversePacket(ppg_red_val_,len(ppg_red_val_)-1)
		
	# 	# temperature
	# 	temp0 = int.from_bytes(data_raw[16:17],byteorder='big',signed=False)
	# 	temp1 = int.from_bytes(data_raw[17:18],byteorder='big',signed=False)
	# 	temp = (temp0 | temp1<<8)/100

	# 	resp_rate = int.from_bytes(data_raw[18:19], byteorder='big',signed=False)
	# 	sp02 = int.from_bytes(data_raw[19:20], byteorder='big',signed=False)
	# 	heart_rate = int.from_bytes(data_raw[20:21], byteorder='big',signed=False)
	# 	# bp = int.from_bytes(data_raw[21:24], byteorder='big',signed=True)
	# 	lead_status = int.from_bytes(data_raw[23:24], byteorder='big',signed=False)

	# 	# check ecg lead status
	# 	lead_status_ecg = lead_status
	# 	lead_status_ecg &= 1
	# 	if (lead_status_ecg == 1):
	# 		print("ECG lead error")
	# 	else:
	# 		print("ECG lead connected")

	# 	lead_status_ppg = lead_status
	# 	lead_status_ppg &= 2
	# 	if (lead_status_ppg == 2):
	# 		print("PPG error")
	# 	else:
	# 		print("PPG connected")


	# 	print("ECG:",ECG)
	# 	print("Respiration Value:",resp_val)
	# 	print("PPG IR Value:",ppg_ir_val)
	# 	print("PPG Red Value:",ppg_red_val)
	# 	print("Temperature:",temp)
	# 	print("Respiration Rate:",resp_rate)
	# 	print("SpO2:",sp02)
	# 	print("Heart Rate:",heart_rate)
	# 	print("SpO2 and ECG lead status:",lead_status)
		
	# 	# data = data_raw.decode()
		
	# 	# print(data)
	# 	if PLOT:
	# 		y_var = np.append(y_var,ppg_ir_val)
	# 		y_var = y_var[1:plot_window+1]
	# 		line.set_ydata(y_var)
	# 		ax.relim()
	# 		ax.autoscale_view()
	# 		fig.canvas.draw()
	# 		fig.canvas.flush_events()

		
	# 	print("loop time:",time.time()-start_time)
	# 	# exit()

def get_parser():
	parser = argparse.ArgumentParser(description="HealthyPiv3 Python data collector")

	parser.add_argument(
		'-v', '--verbose',
		dest='verbose',
		help='Show verbose output',
		action='store_true')
	parser.add_argument(
		'-p','--port',
		dest='port',
		help="HealthyPiv3 Port",
		metavar='PORT'
		)
	parser.add_argument(
		'-c','--csv',
		dest='csv',
		help='Option to output csv',
		action='store_true')
	parser.add_argument(
		'-o','--ouput_folder',
		dest='ouptut_folder',
		help='CSV output folder (default=./data)',
		default='./data',
		metavar='DIR')
	parser.add_argument(
		'-pre','--prefix',
		dest='prefix',
		help='Prefix of output csv files (default=healthypiv3)',
		default='healthypiv3',
		metavar='STR')

	# args = parser.parse_args()
	args = parser.parse_args([
		'-v',
		'-p',COM_PORT,
		'-c',
		])

	# print arguments if verbose
	if args.verbose:
		args_dict = vars(args)
		for key in sorted(args_dict):
			print("{} = {}".format(str(key), str(args_dict[key])))

	return args

if __name__=="__main__":
	args = get_parser()
	main(args)







# while True:
#     try:
#         ser_bytes = ser.readline()
#         try:
#             decoded_bytes = float(ser_bytes[0:len(ser_bytes)-2].decode("utf-8"))
#             print(decoded_bytes)
#         except:
#             continue
#         with open("test_data.csv","a") as f:
#             writer = csv.writer(f,delimiter=",")
#             writer.writerow([time.time(),decoded_bytes])
#         y_var = np.append(y_var,decoded_bytes)
#         y_var = y_var[1:plot_window+1]
#         line.set_ydata(y_var)
#         ax.relim()
#         ax.autoscale_view()
#         fig.canvas.draw()
#         fig.canvas.flush_events()
#     except:
#         print("Keyboard Interrupt")