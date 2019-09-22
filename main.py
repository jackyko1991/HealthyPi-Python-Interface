import serial
import time
import csv
import matplotlib
matplotlib.use("tkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import struct
from collections import deque
import time

def reversePacket(dataPacket,n):
	if n == 0:
		return dataPacket[n]<<(n*8)
	else:
		return (dataPacket[n]<<(n*8))| reversePacket(dataPacket, n-1)

# fast plotting https://gist.github.com/electronut/d5e5f68c610821e311b0
class HealthyPi:
	def __init__(self, port='COM3',plot_window=480):
		self.port = port
		self.baud_rates = 57600
		self.plot_window = plot_window
		# use deque for faster list operations
		self.ax = deque([0.0]*plot_window)
		# self.ay = deque([0.0]*plot_window)

	def open(self):
		# open serial
		self.ser = serial.Serial(self.port, self.baud_rates)
		self.ser.flushInput()

	def add(self, buf, value):
		# add data
		if len(buf) < self.plot_window:
			buf.append(value)
		else:
			buf.pop()
			buf.appendleft(value)

	def update(self, frameNum, a0):
		try:
			data_raw = self.ser.readline()

			if (len(data_raw)==27):
				# PPG
				ppg_ir_val_ = []
				ppg_ir_val_.append(int.from_bytes(data_raw[8:9], byteorder='big',signed=False))
				ppg_ir_val_.append(int.from_bytes(data_raw[9:10], byteorder='big',signed=False))
				ppg_ir_val_.append(int.from_bytes(data_raw[10:11], byteorder='big',signed=False))
				ppg_ir_val_.append(int.from_bytes(data_raw[11:12], byteorder='big',signed=False))
				ppg_ir_val = reversePacket(ppg_ir_val_,len(ppg_ir_val_)-1)

				start_time = time.time()
				self.add(self.ax,ppg_ir_val)
				a0.set_data(range(self.plot_window), self.ax)
				print(time.time() - start_time)
			# if (ppg_ir_val == 0):
			# 	print("error")
			# 	print(data_raw)
			# 	print(len(data_raw))
			# 	exit()
			# else:
			# 	print(ppg_ir_val)
			# 	print(len(data_raw))
				# 			# y_var = np.array(np.zeros([plot_window]))
				# # plt.ion()
				# # 
				# # line, = ax.plot(y_var)

				# ecg = []
				# ir = []
				# red = []

				# while True:
				# 	ECG = int.from_bytes(data_raw[4:6], byteorder='big',signed=True)
				# 	resp_val = int.from_bytes(data_raw[6:8], byteorder='big',signed=True)
					

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

				# 	# ppg_ir_val = int.from_bytes(data_raw[8:12], byteorder='big',signed=True)
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

				# 	# print()
				# 	# temp = int.from_bytes(data_raw[16:18], byteorder='big',signed=True)
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

				# 	# exit()


				# 	print("ECG:",ECG)
				# 	print("Respiration Value:",resp_val)
				# 	print("PPG IR Value:",ppg_ir_val)
				# 	print("PPG Red Value:",ppg_red_val)
				# 	print("Temperature:",temp)
				# 	print("Respiration Rate:",resp_rate)
				# 	print("SpO2:",sp02)
				# 	print("Heart Rate:",heart_rate)
				# 	print("SpO2 and ECG lead status:",lead_status)
				# 	# SpO2 = int.from_bytes(data_raw[20:21], byteorder='big', signed=True)
				# 	# print(SpO2)
					
				# 	# data = data_raw.decode()
					
				# 	# print(data)

				# 	# y_var = np.append(y_var,ppg_ir_val)
				# 	# y_var = y_var[1:plot_window+1]
				# 	# line.set_ydata(y_var)
				# 	# ax.relim()
				# 	# ax.autoscale_view()
				# 	# fig.canvas.draw()
				# 	# fig.canvas.flush_events()
				# 	# exit()
		except KeyboardInterrupt:
			print("exiting")

		return a0

	def close(self):
		# close port
		self.ser.flush()
		self.ser.close()

def main():
	healthyPi = HealthyPi('COM3',480)
	healthyPi.open()

	# animation stuffs
	fig = plt.figure()
	ax = plt.axes(xlim=(0, 480), ylim=(1e8, 3e9))
	# fig, ax = plt.subplots()
	line0 = ax.plot([],[])
	anim = animation.FuncAnimation(fig,healthyPi.update,
		fargs=(line0),
		interval=10)
	plt.show()

	# cleanup
	healthyPi.close()



if __name__=="__main__":
	main()







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