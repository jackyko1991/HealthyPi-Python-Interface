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

def reversePacket(dataPacket,n):
	if n == 0:
		return dataPacket[n]<<(n*8)
	else:
		return (dataPacket[n]<<(n*8))| reversePacket(dataPacket, n-1)

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
		start_time = datetime.datetime.now()
		while self.event.is_set():
			raw_data = self.serial.readline()

			# received data should be 27 bytes
			if not len(raw_data) == 27:
				continue

			# get current datatime
			dt = str(datetime.datetime.now())
			# elapsed_time in second:
			elapsed_time = str((datetime.datetime.now() - start_time).total_seconds())
			# convert raw data to human readable values, reference: http://healthypi.protocentral.com/ "Streaming Packet Format"
			ecg = raw2int(raw_data,5,6)
			resp = raw2int(raw_data,7,8)
			ppg_ir = raw2int(raw_data,9,12)
			ppg_red = raw2int(raw_data,13,16)
			temp = raw2int(raw_data,17,18)/100
			resp_rate = int.from_bytes(raw_data[18:19], byteorder='big',signed=False)
			spo2 = int.from_bytes(raw_data[19:20], byteorder='big',signed=False)
			heart_rate = int.from_bytes(raw_data[20:21], byteorder='big',signed=False)
			# bp not implemented
			# bp = int.from_bytes(data_raw[21:24], byteorder='big',signed=True)
			lead_status = int.from_bytes(raw_data[23:24], byteorder='big',signed=False)

			# check ecg lead status
			lead_status_ecg = lead_status
			lead_status_ecg &= 1
			lead_status_ppg = lead_status
			lead_status_ppg &= 2

			data = {
				"time":elapsed_time, 
				"ecg":ecg,
				"resp":resp,
				"ppg_ir":ppg_ir,
				"ppg_red":ppg_red,
				"temp":temp,
				"resp_rate":resp_rate,
				"spo2":spo2,
				"heart_rate":heart_rate,
				"lead_status_ecg":lead_status_ecg,
				"lead_status_ppg":lead_status_ppg
			}

			self.data.append(data)

			if self.verbose:
				print(dt + ": ")
				print("ECG Value:",ecg)
				print("Respiration Value:",resp)
				print("PPG IR Value:",ppg_ir)
				print("PPG Red Value:",ppg_red)
				print("Temperature:",temp)
				print("Respiration Rate:",resp_rate)
				print("SpO2:",spo2)
				print("Heart Rate:",heart_rate)
				# print("SpO2 and ECG lead status:",lead_status)
				if (lead_status_ecg == 1):
					print("ECG lead error")
					lead_status_ecg = 0
				else:
					print("ECG lead connected")
					lead_status_ecg = 1
				if (lead_status_ppg == 2):
					print("PPG error")
					lead_status_ppg = 0
				else:
					print("PPG connected")
					lead_status_ppg = 1

			# write to csv
			if self.signals_csv_writer is not None:
				signals_row = {
					'Time [s]': elapsed_time,
					' RESP': resp,
					' PLETH': ppg_ir,
					' II': ecg,
					' Status ECG': lead_status_ecg,
					' Status PPG': lead_status_ppg
				}
				self.signals_csv_writer.writerow(signals_row)

			if self.numerics_csv_writer is not None:
				numerics_row = {
					'Time [s]': elapsed_time, 
					' HR': heart_rate, 
					' PULSE': heart_rate, 
					' RESP': resp_rate, 
					' SpO2': spo2,
					' Status ECG': lead_status_ecg,
					' Status PPG': lead_status_ppg
				}
				self.numerics_csv_writer.writerow(numerics_row)

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
		signalsWriter = csv.DictWriter(signalsCsv, fieldnames = ["Time [s]", " RESP", " PLETH", " II", " Status ECG", " Status PPG"])
		numericsWriter = csv.DictWriter(numericsCsv, fieldnames = ["Time [s]", " HR", " PULSE", " RESP", " SpO2", " Status ECG", " Status PPG"])
		signalsWriter.writeheader()
		numericsWriter.writeheader()

	data = deque([])
	lock = threading.Lock()

	running_event = threading.Event()
	running_event.set()

	collector = HealthyPiCollector(data,args.port,lock,running_event,verbose=True)
	collector.verbose=args.verbose

	if args.csv:
		collector.signals_csv_writer = signalsWriter
		collector.numerics_csv_writer = numericsWriter
	collector.open()
	collector.start()

	if args.graph:
		plot_window = args.window
		y_ecg = np.array(np.zeros([plot_window]))
		y_ppg = np.array(np.zeros([plot_window]))
		y_resp = np.array(np.zeros([plot_window]))
		plt.ion()
		fig, axs = plt.subplots(3,1)
		line_ecg = axs[0].plot(y_ecg)
		line_ppg = axs[1].plot(y_ppg)
		line_resp = axs[2].plot(y_resp)
		axs[0].set_xlim(0, plot_window)
		axs[1].set_xlim(0, plot_window)
		axs[2].set_xlim(0, plot_window)
		plt.show()
		
	while True:
		try:
			# need to give some blocking time main thread to intercept keyboard interrupt
			collector.join(0.0001)
			if args.graph:
				y_ecg = np.append(y_ecg,collector.data[-1]["ecg"])
				y_ecg = y_ecg[1:plot_window+1]
				y_ppg = np.append(y_ppg,collector.data[-1]["ppg_ir"])
				y_ppg = y_ppg[1:plot_window+1]
				y_resp = np.append(y_resp,collector.data[-1]["resp"])
				y_resp = y_resp[1:plot_window+1]
				line_ecg[0].set_ydata(y_ecg)
				line_ppg[0].set_ydata(y_ppg)
				line_resp[0].set_ydata(y_resp)
				axs[0].relim()
				axs[0].autoscale_view()
				axs[1].relim()
				axs[1].autoscale_view()
				axs[2].relim()
				axs[2].autoscale_view()
				fig.canvas.draw()
				fig.canvas.flush_events()

		except KeyboardInterrupt:
			print("Stopping data collection, wait till serial port close...")
			if args.graph:
				plt.close(fig)
			running_event.clear()
			collector.join()
			collector.close()
			if args.csv:
				signalsCsv.close()
				numericsCsv.close()

			print("Stopped data collection")
			sys.exit()

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
	parser.add_argument(
		'-g','--graph',
		dest='graph',
		help='Plot the data collection graph',
		action='store_true')
	parser.add_argument(
		'-w','--window',
		dest='window',
		help="Plotting window width (default=60)",
		default=60,
		metavar='INT')

	args = parser.parse_args()
	# args = parser.parse_args([
	# 	'-v',
	# 	'-p','COM3',
	# 	'-c',
	# 	'-g',
	# 	])

	# print arguments if verbose
	if args.verbose:
		args_dict = vars(args)
		for key in sorted(args_dict):
			print("{} = {}".format(str(key), str(args_dict[key])))

	return args

if __name__=="__main__":
	args = get_parser()
	main(args)