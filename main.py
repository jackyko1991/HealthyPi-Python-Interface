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

def raw2int(raw,offset_start,offset_end):
	val_ = []
	for i in range(offset_start,offset_end+1):
		val_.append(int.from_bytes(raw[i-1:i],byteorder='big',signed=False))
	val = reversePacket(val_,len(val_)-1)

	return val

class HealthyPiCollector(threading.Thread):
	"""
		The HealthyPi class will spawn a sparate thread to avoid main thread blocking during data collection
	"""
	def __init__(self,data,port,lock,event,baud_rate=57600,signals_csv_writer=None,numerics_csv_writer=None, verbose=False):
		super(HealthyPiCollector, self).__init__()
		self.data = data
		self.port = port
		self.lock = lock
		self.event = event
		self.baud_rate = baud_rate
		self.serial = None
		self.signals_csv_writer = signals_csv_writer
		self.numerics_csv_writer = numerics_csv_writer
		self.verbose = verbose

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

			# received data should be 27 bytes
			if not len(raw_data) == 27:
				continue

			# get current datatime
			dt = str(datetime.datetime.now())

			# convert raw data to human readable values, reference: http://healthypi.protocentral.com/ "Streaming Packet Format"
			ecg = raw2int(raw_data,5,6)
			resp = raw2int(raw_data,7,8)
			ppg_ir = raw2int(raw_data,9,12)
			ppg_red = raw2int(raw_data,13,16)
			temp = raw2int(raw_data,17,18)/100
			resp_rate = int.from_bytes(raw_data[18:19], byteorder='big',signed=False)
			sp02 = int.from_bytes(raw_data[19:20], byteorder='big',signed=False)
			heart_rate = int.from_bytes(raw_data[20:21], byteorder='big',signed=False)
			# bp not implemented
			# bp = int.from_bytes(data_raw[21:24], byteorder='big',signed=True)
			lead_status = int.from_bytes(raw_data[23:24], byteorder='big',signed=False)

			if self.verbose:
				print(dt + ": ")
				print("ECG Value:",ecg)
				print("Respiration Value:",resp)
				print("PPG IR Value:",ppg_ir)
				print("PPG Red Value:",ppg_red)
				print("Temperature:",temp)
				print("Respiration Rate:",resp_rate)
				print("SpO2:",sp02)
				print("Heart Rate:",heart_rate)
				print("SpO2 and ECG lead status:",lead_status)

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




			

def main(args):
	### CSV part
	if args.csv:
		# create folder for data export
		if not os.path.exists(args.ouptut_folder):
			os.makedirs(args.ouptut_folder)

		# create csv files
		dt = datetime.datetime.now()
		datetime_str = dt.strftime("%Y%m%d-%H%M%S")
		signalsCsv = open(args.ouptut_folder + "/"+ args.prefix + "_" + datetime_str + "_Signals.csv",'w',newline='')
		numericsCsv = open(args.ouptut_folder + "/"+ args.prefix + "_" + datetime_str + "_Numerics.csv",'w',newline='')
		signalsWriter = csv.DictWriter(signalsCsv, fieldnames = ["Time [s]", "RESP", "PLETH", "II"])
		numericsWriter = csv.DictWriter(numericsCsv, fieldnames = ["Time [s]", "HR", "PULSE", "RESP", "SpO2"])
		signalsWriter.writeheader()
		numericsWriter.writeheader()

	data = deque([])
	lock = threading.Lock()

	running_event = threading.Event()
	running_event.set()

	collector = HealthyPiCollector(data,args.port,lock,running_event,verbose=True)
	collector.open()
	collector.start()

	while True:
		try:
			print("hello")
			collector.join(0.1)
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
		# '-c',
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