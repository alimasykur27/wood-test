import json
import random
import pyaudio
import scipy.io.wavfile as wavfile
import wave
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import noisereduction as nr
from spectrum import *
from matplotlib.ticker import MultipleLocator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog, QHeaderView, QTableWidgetItem
from ui_mainwindow import Ui_MainWindow
from Recorder import Recorder

class MainWindow(QMainWindow):
    ui = None
    recorder = None
    devices = None
    path = "audio/"

    def __init__(self, parent=None):
        """
        Constructor
        """
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.recorder = Recorder()

        # === Background Tab ===
        # add device list to combobox
        self.devices = self.get_device_list()
        for device in self.devices:
            self.ui.pilihMD.addItem(device['name'])
            self.ui.pilihMJ.addItem(device['name'])

        # set default device index
        self.set_device_id()

        # get combobox index and save to variable
        self.ui.pilihMD.currentIndexChanged.connect(self.set_device_id)
        self.ui.pilihMJ.currentIndexChanged.connect(self.set_device_id)

        # Record button clicked and callback function with parameter
        self.ui.pbBG.clicked.connect(lambda: self.process("background")) # udah langsung ke noise reduction

        # Noise Reduction button clicked and callback function with parameter
        # self.ui.noiseBG.clicked.connect(lambda: self.noiseReduction("background"))
        # self.ui.pbBG.clicked.connect(lambda: self.noiseReduction("background"))

        # Upload file button clicked and callback function
        self.ui.pbBGUpload.clicked.connect(lambda: self.uploadBGAudio())

        # === Kayu Tab ===
        # add device list to combobox
        self.devices = self.get_device_list()
        for device in self.devices:
            self.ui.pilihMDK.addItem(device['name'])
            self.ui.pilihMJK.addItem(device['name'])

        # set default device index
        self.set_device_id()

        # get combobox index and save to variable
        self.ui.pilihMDK.currentIndexChanged.connect(self.set_device_id)
        self.ui.pilihMJK.currentIndexChanged.connect(self.set_device_id)

        # Record button clicked and callback function with parameter
        self.ui.pbKayu.clicked.connect(lambda: self.process("kayu")) # udah langsung ke noise reduction

        # Noise Reduction button clicked and callback function with parameter for testing
        # self.ui.pbKayu.clicked.connect(lambda: self.noiseReduction("kayu"))
        self.ui.pbKayu_analyze.clicked.connect(lambda: self.UploadKayuAudio()) # langsung ke analysis tanpa record

        # === Analysis Tab ===
        # Upload file button clicked and callback function
        self.ui.pbUpload.clicked.connect(lambda: self.getAudioFile())

        # Refresh button clicked and callback function
        self.ui.pbRefresh.clicked.connect(lambda: self.refresh_plot())

        # Hapus button clicked and callback function
        self.ui.pbHapus.clicked.connect(lambda: self.clearAudioFile())

        # === Table ===
        # set table header
        print("=====\t Table \t=====")
        print("set table header")
        self.ui.tableAnalysis.setColumnCount(3)
        self.ui.tableAnalysis.setHorizontalHeaderLabels(["Nama Kayu", "Frekuensi Resonansi", "Kelas Kuat"])
        self.ui.tableAnalysis.horizontalHeader().setVisible(True)

        # fit table to content
        print("fit table to content")
        self.ui.tableAnalysis.horizontalHeader().setStretchLastSection(True)
        self.ui.tableAnalysis.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def process(self, type=None):
        """
        Process audio
        """
        print("=====\t Process \t=====")
        # record audio
        self.record(type=type)

        # get audio file
        if type == None:
            file_MD = self.path + "output_MD.wav"
            file_MJ = self.path + "output_MJ.wav"
        elif type == "background":
            file_MD = self.path + "background_MD.wav"
            file_MJ = self.path + "background_MJ.wav"
        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            if wood == "" or wood == None:
                wood = "kayu"

            file_MD = self.path + wood + "_MD.wav"
            file_MJ = self.path + wood + "_MJ.wav"

        # show audio waveform
        if type == None:
            self.plot(index=1, type="output", file_name=file_MD)
            self.plot(index=2, type="output", file_name=file_MJ)
        elif type == "background" or type == "kayu":
            self.plot(index=1, type=type, file_name=file_MD)
            self.plot(index=2, type=type, file_name=file_MJ)

        self.noiseReduction(type=type)

    def UploadKayuAudio(self):
        """
        Analyze audio
        """
        print("=====\t Analyze \t=====")
        # get wood name
        wood_name = self.ui.namaKayu.text()
        if wood_name == "" or wood_name == None:
            wood_name = "kayu"

        # get audio file
        file_MD = self.path + wood_name + "_MD.wav"
        file_MJ = self.path + wood_name + "_MJ.wav"

        # show audio waveform
        self.plot(index=1, type="kayu", file_name=file_MD)
        self.plot(index=2, type="kayu", file_name=file_MJ)

        # show audio fft
        self.plotfft(type="kayu")

        # Analyze audio
        self.analysis()

    def uploadBGAudio(self):
        """
        Upload background audio
        """
        print("=====\t Upload \t=====")
        # get audio file
        file_MD = self.path + "background_MD.wav"
        file_MJ = self.path + "background_MJ.wav"

        # show audio waveform
        self.plot(index=1, type="background", file_name=file_MD)
        self.plot(index=2, type="background", file_name=file_MJ)

        # show audio fft
        self.plotfft(type="background")

    def record(self, type=None):
        """
        Record audio
        """
        print("=====\t Record \t=====")
        # record audio and save to file
        if type == None:
            self.recorder.setFilename_MD("output_MD.wav")
            self.recorder.setFilename_MJ("output_MJ.wav")

        elif type == "background":
            self.recorder.setFilename_MD("background_MD.wav")
            self.recorder.setFilename_MJ("background_MJ.wav")

        elif type == "kayu":
            wood_name = self.ui.namaKayu.text()
            if wood_name == "" or wood_name == None:
                wood_name = "kayu"

            filename1 = wood_name + "_MD.wav"
            filename2 = wood_name + "_MJ.wav"
            self.recorder.setFilename_MD(filename1)
            self.recorder.setFilename_MJ(filename2)

        try:
            self.recorder.record()
        except Exception as e:
            print("[Process Error]: " + e.__str__())

        self.recorder.save()

    def noiseReduction(self, type=None):
        """
        Noise Reduction
        """
        print("=====\t Noise Reduction \t=====")

        # get audio and noise
        if type == "background":
            audio_file = self.path + "background_MJ.wav"
            noise_file = self.path + "background_MD.wav"

        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            if wood == "" or wood == None:
                wood = "kayu"
            else:
                wood = self.ui.namaKayu.text()
            
            audio_file = self.path + wood + "_MJ.wav"
            noise_file = self.path + wood + "_MD.wav"
        
        elif type == "kayu-bg":
            wood = self.ui.namaKayu.text()
            if wood == "" or wood == None:
                wood = "kayu"
            else:
                wood = self.ui.namaKayu.text()

            audio_file = self.path + wood + "_MJ.wav"
            noise_file = self.path + "background_fft.wav"
        
        # load audio and noise
        samprate_audio, audio = nr.read_audio(audio_file)
        samprate_noise, noise = nr.read_audio(noise_file)

        audio = audio.astype(float)
        noise_clip = nr.generate_noise_sample(noise=noise, samprate_noise=samprate_noise, length=len(audio))
        
        # noise reduction
        if type == "background":
            bg_fft = nr.noise_reduction(audio=audio, noise_clip=noise_clip, fft_size=4096, iterations=3)
            self.save_fft(filename="background_fft.wav", output=bg_fft)
        
        elif type == "kayu":
            kayu_fft = nr.noise_reduction(audio=audio, noise_clip=noise_clip, fft_size=4096, iterations=3)
            self.save_fft(filename=wood + "_fft.wav", output=kayu_fft)

            # noise reduction kayu - background
            self.noiseReduction(type="kayu-bg")
        
        elif type == "kayu-bg":
            kayu_bg_fft = nr.noise_reduction_final(audio=audio, noise_clip=noise_clip, fft_size=4096, iterations=7)
            self.save_fft(filename=wood + ".wav", output=kayu_bg_fft)

            # Analysis
            self.analysis()

        # show audio waveform
        if type == "background":
            self.plotfft(type="background")
        elif type == "kayu":
            self.plotfft(type="kayu")
        
    def analysis(self):
        """
        Analysis
        """
        print("=====\t Analysis \t=====")

        # get audio
        wood_name = self.ui.namaKayu.text()
        if wood_name == "" or wood_name == None:
            wood_name = "kayu"
        else:
            wood_name = self.ui.namaKayu.text()

        audio_name = self.path + wood_name + ".wav"

        # load audio
        fs, data = wavfile.read(audio_name)
        convertFromPSD = 10**(-75/20)
        dB = data*convertFromPSD

        # get sinyal psd
        from pylab import psd
        sinyal = psd(dB, NFFT=4096, Fs=fs)

        # get resonance frequency
        res_freq = self.get_resonance_freq(sinyal)
        print("Resonance Frequency: " + str(res_freq))

        # get class
        res_class = self.get_wood_class(res_freq)
        print("Class: " + res_class)

        # show result
        self.ui.name_label.setText(wood_name)
        self.ui.frequency_label.setText(str(res_freq))
        self.ui.kelas_label.setText(res_class)

        # save to database
        self.save_to_json(wood_name, res_freq, res_class)

    def save_to_json(self, name, freq, res_class):
        """
        Save to json
        """
        print("=====\t Save to JSON \t=====")

        data = {
            "filename": name + ".wav", 
            "name": name,
            "frequency": freq,
            "class": res_class
        }

        # add new data to current json data if json file exist. 
        # if not exist, create new json file

        if os.path.exists("data.json"):
            with open("data.json", "r") as f:
                json_data = json.load(f)

                # if json file exist, but data is empty
                if len(json_data) == 0 or json_data == None:
                    json_data.append(data)
                
                else:
                    # check if data already exist
                    for i in json_data:
                        if i["name"] == data["name"] and i["frequency"] == data["frequency"] and i["class"] == data["class"]:
                            return            
                        else:
                            json_data.append(data)
            
            with open("data.json", "w") as f:
                json.dump(json_data, f)

        else:
            with open("data.json", "w") as f:
                json.dump([data], f)

    def get_data_json(self, name=None):
        """
        Get data from json
        """
        print("=====\t Get Data from JSON \t=====")

        if os.path.exists("data.json") and name != None:
            with open("data.json", "r") as f:
                json_data = json.load(f)
                # if json file exist, but data is empty return None
                if len(json_data) == 0 or json_data == None:
                    return None
                else:
                    if name == "All":
                        return json_data
                    else:
                        for i in json_data:
                            if i["name"] == name:
                                return i
                        return None
        else:
            return None

    def get_resonance_freq(self, sinyal):
        n = len(sinyal[0])
        sorted_data0 = sorted(sinyal[0], reverse=True)
        max_data = -9999
        max_freq = -9999

        for i in range(0, n):
            # get freq index of max data
            idx = np.where(sinyal[0] == sorted_data0[i])
            tmp_freq = sinyal[1][idx]
            if tmp_freq > 0 and tmp_freq < 6000:
                m = 10 * np.log10(sorted_data0[i])
                if m > -115:
                    if tmp_freq > max_freq:
                        max_data = m
                        max_freq = tmp_freq

        return max_freq[0]

    def get_wood_class(self, freq):
        if freq < 2250:
            return "1"
        elif freq < 3000:
            return "2"
        elif freq < 3500:
            return "3"
        elif freq < 5000:
            return "4"
        else:
            return "5"

    def getAudioFile(self):
        """
        Get audio file
        """
        print("=====\t Get Audio File \t=====")
        file, _ = QFileDialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.wav)")
        
        print("Get Audio File: " + file)
        self.ui.file_list.addItem(file)

        self.refresh_plot()

    def clearAudioFile(self):
        """
        Clear audio file that choosen
        """
        print("=====\t Clear Audio File \t=====")
        for i in range(self.ui.file_list.count()):
            try:
                selected = self.ui.file_list.item(i).isSelected()
            except:
                selected = False

            if selected:
                # clear item selected
                print("Clear Audio File: " + self.ui.file_list.item(i).text())
                self.ui.file_list.takeItem(i)
            else:
                print("No Audio File Selected")
        
        self.refresh_plot()

    def save_fft(self, filename=None, output=None):
        print("Save FFT: " + filename)

        if filename == None:
            filename = "output_fft.wav"
        
        wavfile.write(self.path + filename, 44100, output.astype(np.int16))

    def plot(self, index=None, type=None, file_name=None):
        if type == "background":
            print("Plot Background")
        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            print("Plot Kayu " + wood)

        size = (7, 3)
        scene = self.draw_plot(audio_name=file_name, size=size)

        if type == "background":
            if index == 1:
                self.ui.mdBG.setScene(scene)
            elif index == 2:
                self.ui.mjBG.setScene(scene)
        elif type == "kayu":
            if index == 1:
                self.ui.mdKayu.setScene(scene)
            elif index == 2:
                self.ui.mjKayu.setScene(scene)
    
    def plotfft(self, type=None):
        if type == "background":
            print("Plot Background FFT")
            audio = self.path + "background_fft.wav"

        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            print("Plot Kayu " + wood + " FFT")
            audio = self.path + wood + ".wav"
        
        size = (12, 4)
        scene = self.draw_plotfft(audio_name=audio, size=size)
        
        if type == "background":
            self.ui.fftBG.setScene(scene)
        elif type == "kayu":
            self.ui.fftKayu.setScene(scene)

    def draw_plot(self, audio_name=None, size=None):
        """
        Plot the audio signal in time domain
        param audio_name: audio file name
        param size: size of plot
        return scene: plot in scene
        """
        
        if audio_name == None:
            return

        # Plot the audio signal in time
        x, sr = librosa.load(audio_name)

        # size in px
        figure = plt.figure(figsize=size, dpi=100)
        axes = figure.gca()
        librosa.display.waveshow(x, sr)
        axes.set_title('Audio Signal in Time Domain', size=10)
        axes.set_xlabel('Time (s)', size=8)
        axes.set_ylabel('Amplitude (dB)', size=8)
        
        # put figure to center of scene
        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        return scene
    
    def draw_plotfft(self, audio_name=None, size=None):
        """
        Plot the audio signal in frequency domain
        param audio_name: audio file name
        param size: size of plot
        return scene: plot in scene
        """
        if audio_name == None:
            return

        # Plot the audio signal in frequency domain
        fs, data = wavfile.read(audio_name)
        convertFromPSD = 10 ** (-75/20)
        dB = data*convertFromPSD
        
        # size in px
        figure = plt.figure(figsize=size, dpi=100)
        axes = figure.gca()
        p = WelchPeriodogram(dB, NFFT=2048, sampling=fs, label=audio_name)
        axes.set_title('Audio Signal in Frequency Domain', size=13)
        axes.set_xlabel('Frequency (Hz)', size=10)
        axes.set_ylabel('Amplitude (dB)', size=10)
        axes.set_xlim(0, 6000)
        axes.xaxis.set_major_locator(MultipleLocator(250))
        axes.yaxis.set_major_locator(MultipleLocator(5))

        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        return scene

    def refresh_plot(self):
        """
        Refresh plot for Frequency Analysis
        """
        print("Refresh Plot")

        # remove table 
        self.remove_data_table()
    
        # Get audio file from list store to list
        audio_db = []
        audio_name = []
        fs_list = []

        for i in range(self.ui.file_list.count()):
            tmp_name = self.ui.file_list.item(i).text()
            tmp_fs, tmp_data = wavfile.read(tmp_name)
            tmp_convertFromPSD = 10 ** (-70/20)
            tmp_dB = tmp_data*tmp_convertFromPSD

            fs_list.append(tmp_fs)
            audio_db.append(tmp_dB)

            # parse to get .wav name
            tmp_name = tmp_name.split("/")[-1]
            tmp_name = tmp_name.split(".")[0]
            audio_name.append(tmp_name)

            # get data analysis
            from pylab import psd
            sinyal = psd(tmp_dB, NFFT=4096, Fs=tmp_fs)

            # get resonance frequency
            res_freq = self.get_resonance_freq(sinyal)
            print("Resonance Frequency: " + str(res_freq))

            # get class
            res_class = self.get_wood_class(res_freq)
            print("Class: " + res_class)

            analyzed_data = {
                "file_name": tmp_name + ".wav",
                "name": tmp_name,
                "frequency": res_freq,
                "class": res_class
            }

            # add to table
            self.add_to_table(data=analyzed_data)

        # Plot the audio signal in frequency domain
        # size fit to QGraphicView, size to plt.figure is in inch
        h, w = self.ui.fftMulti.size().height(), self.ui.fftMulti.size().width() + 50
        size = (w/100, h/100)
        figure = plt.figure(figsize=size, dpi=100)
        axes = figure.gca()
        
        for i in range(len(audio_db)):
            color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])

            p = WelchPeriodogram(
                audio_db[i], 
                NFFT=2048, 
                sampling=fs_list[i], 
                label=audio_name[i], 
                color=color)

            axes.legend(loc='upper right', fontsize=8)

        axes.set_title('Audio Signal in Frequency Domain', size=15)
        axes.set_xlabel('Frequency (Hz)', size=12)
        axes.set_ylabel('Amplitude (dB)', size=12)
        axes.set_xlim(0, 6000)
        axes.xaxis.set_major_locator(MultipleLocator(250))
        axes.yaxis.set_major_locator(MultipleLocator(5))

        # set scene size
        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        self.ui.fftMulti.setScene(scene)

    def add_to_table(self, data=None):
        """
        Add data to table
        """
        if data == None:
            return

        # add to table
        rowPosition = self.ui.tableAnalysis.rowCount()
        self.ui.tableAnalysis.insertRow(rowPosition)
        self.ui.tableAnalysis.setItem(rowPosition, 0, QTableWidgetItem(data['name']))
        self.ui.tableAnalysis.setItem(rowPosition, 1, QTableWidgetItem(str(data['frequency'])))
        self.ui.tableAnalysis.setItem(rowPosition, 2, QTableWidgetItem(data['class']))

    def remove_data_table(self):
        """
        Remove all data from table
        """
        print("Remove data")
        self.ui.tableAnalysis.clearContents()
        self.ui.tableAnalysis.setRowCount(0)

    def get_device_list(self):
        # Dapatkan jumlah perangkat audio yang tersedia
        num_devices = self.recorder.p.get_device_count()

        # create list of devices dictionary
        devices = []

        # Tampilkan daftar mikrofon yang tersedia
        # add index and name to dictionary
        # print("Daftar mikrofon yang tersedia:"
        for i in range(num_devices):
            info = self.recorder.p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print("Input Device id ", i, " - ", info['name'])
                devices.append({'device_id': i, 'name': info['name']})

        return devices

    def set_device_id(self):
        # get combobox index and save to variable
        print("Device changed")

        index_D = self.devices[self.ui.pilihMD.currentIndex()]['device_id']
        index_J = self.devices[self.ui.pilihMJ.currentIndex()]['device_id']
        print(f"Device D: {index_D}")
        print(f"Device J: {index_J}")

        self.recorder.setDeviceID_1(device_id=index_D)
        self.recorder.setDeviceID_2(device_id=index_J)