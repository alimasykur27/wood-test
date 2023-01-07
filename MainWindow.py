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
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog
from ui_mainwindow import Ui_MainWindow
from Recorder import Recorder

class MainWindow(QMainWindow):
    ui = None
    rrecorder = None
    devices = None

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

        # Noise Reduction button clicked and callback function with parameter
        # self.ui.noiseKayu.clicked.connect(lambda: self.noiseReduction("kayu"))

        # === FFT Tab ===
        # Upload file button clicked and callback function
        self.ui.pbUpload.clicked.connect(lambda: self.getAudioFile())

        # Refresh button clicked and callback function
        self.ui.pbRefresh.clicked.connect(lambda: self.refresh_plot())

        # Hapus button clicked and callback function
        self.ui.pbHapus.clicked.connect(lambda: self.clearAudioFile())


    def process(self, type=None):
        """
        Process audio
        """
        print("=====\t Process \t=====")
        # record audio
        self.record(type=type)

        # show audio waveform
        if type == None:
            self.plot(index=1, type="output")
            self.plot(index=2, type="output")
        elif type == "background" or type == "kayu":
            self.plot(index=1, type=type)
            self.plot(index=2, type=type)

        self.noiseReduction(type=type)

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
            audio = "background_MJ.wav"
            noise = "background_MD.wav"

        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            if wood == "" or wood == None:
                wood = "kayu"
            else:
                wood = self.ui.namaKayu.text()
            
            audio = wood + "_MJ.wav"
            noise = wood + "_MD.wav"
        
        elif type == "kayu-bg":
            wood = self.ui.namaKayu.text()
            if wood == "" or wood == None:
                wood = "kayu"
            else:
                wood = self.ui.namaKayu.text()

            audio = wood + "_fft.wav"
            noise = "background_fft.wav"
        
        # load audio and noise
        samprate_audio, audio = nr.read_audio(audio)
        samprate_noise, noise = nr.read_audio(noise)

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
            self.save_fft(filename=wood + "_final_fft.wav", output=kayu_bg_fft)

        # show audio waveform
        if type == "background":
            self.plotfft(type="background")
        elif type == "kayu":
            self.plotfft(type="kayu")

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

        wavfile.write(filename, 44100, output.astype(np.int16))

    def plot(self, index=None, type=None):
        if type == "background":
            print("Plot Background")
        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            print("Plot Kayu " + wood)

        if index == 1:
            audio = self.recorder.getFilename_1()
        elif index == 2:
            audio = self.recorder.getFilename_2()

        size = (7, 3)
        scene = self.draw_plot(audio_name=audio, size=size)

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
            audio = "background_fft.wav"

        elif type == "kayu":
            wood = self.ui.namaKayu.text()
            print("Plot Kayu " + wood + " FFT")
            audio = wood + "_final_fft.wav"
        
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
        convertFromPSD = 10 ** (-80/20)
        dB = data*convertFromPSD
        
        # size in px
        figure = plt.figure(figsize=size, dpi=100)
        axes = figure.gca()
        p = WelchPeriodogram(dB, NFFT=2048, sampling=fs, label=audio_name)
        axes.set_title('Audio Signal in Frequency Domain', size=13)
        axes.set_xlabel('Frequency (Hz)', size=10)
        axes.set_ylabel('Amplitude (dB)', size=10)
        axes.set_xlim(0, 22000)
        axes.xaxis.set_major_locator(MultipleLocator(2000))
        axes.yaxis.set_major_locator(MultipleLocator(5))

        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        return scene

    def refresh_plot(self):
        """
        Refresh plot for Frequency Analysis
        """
        print("Refresh Plot")
    
        # Get audio file from list store to list
        audio_db = []
        audio_name = []
        fs_list = []

        for i in range(self.ui.file_list.count()):
            tmp_name = self.ui.file_list.item(i).text()
            tmp_fs, tmp_data = wavfile.read(tmp_name)
            tmp_convertFromPSD = 10 ** (-80/20)
            tmp_dB = tmp_data*tmp_convertFromPSD
            fs_list.append(tmp_fs)
            audio_db.append(tmp_dB)

            # parse to get .wav name
            tmp_name = tmp_name.split("/")[-1]
            tmp_name = tmp_name.split(".")[0]
            audio_name.append(tmp_name)

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
        axes.set_xlim(0, 5000)
        axes.xaxis.set_major_locator(MultipleLocator(250))
        axes.yaxis.set_major_locator(MultipleLocator(5))

        # set scene size
        scene = QGraphicsScene()
        scene.addWidget(FigureCanvas(figure))

        self.ui.fftMulti.setScene(scene)

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