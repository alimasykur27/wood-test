import wave
import contextlib
import numpy as np
import librosa
import librosa.display
import time
import scipy
import matplotlib.pyplot as plt
from datetime import timedelta
from scipy.io import wavfile


def _stft(y, n_fft, hop_length, win_length):
    return librosa.stft(y=y, n_fft=n_fft, hop_length=hop_length, win_length=win_length)

def _istft(y, hop_length, win_length):
    return librosa.istft(y, hop_length, win_length)

def _amp_to_db(x):
    return librosa.core.amplitude_to_db(x, ref=1.0, amin=1e-20, top_db=80.0)

def _db_to_amp(x,):
    return librosa.core.db_to_amplitude(x, ref=1.0)

def get_parameters(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        pcm_data = wf.readframes(wf.getnframes())
        return num_channels, sample_width, sample_rate, type(pcm_data)

def read_audio(path=None):
    if path is None:
        path = "output.wav"
    
    samprate_audio, audio = wavfile.read(path)
    num_channels, samp_width, samp_rate, type = get_parameters(path)
    if num_channels != 1:
        audio = audio[:, 1]
    return samprate_audio, audio

def generate_noise_sample(noise, samprate_noise, length):
    """
    Generate a random sample of noise with the same length as the audio clip
    """
    noise_clip = noise[:samprate_noise*length]
    noise_clip = np.asarray(noise_clip, dtype=float)
    return noise_clip

# def plot_signals(audio, noise):

#     plt.figure(figsize=(14, 14))
#     ax1 = plt.subplot(211)
#     plt.plot(audio)
#     plt.title("Original Signal")

#     ax2 = plt.subplot(212)
#     plt.plot(noise)
#     plt.title("Noise Signal")


def plot_spectrogram(signal, title):
    plt.figure(figsize=(20, 4))
    librosa.display.specshow(signal, sr=44100, x_axis='time', y_axis='hz')
    plt.title(title)
    plt.colorbar()
    plt.show()


def plot_statistics_and_filter(mean_noise, std_noise, noise_th):
    fig, ax = plt.subplots(figsize=(20, 5))
    plt_mean, = ax.plot(mean_noise, label='Rata-rata noise')
    # plt_std, = ax.plot(std_noise, label='Std. power of noise')
    plt_std, = ax.plot(noise_th, label='Threshold noise')
    ax.set_title('Threshold untuk mask')
    ax.legend()
    plt.show()


def remove_noise(audio, 
                noise_clip, 
                n_grad_freq=2, 
                n_grad_time=4, 
                n_fft=2048, 
                win_length=2048, 
                hop_length=512,
                n_std_th=1.5, 
                prop_decrease=0, 
                verbose=False, 
                visual=False):

    """
    Remove noise from audio signal using spectral subtraction
    :param audio: audio signal
    :param noise_clip: noise signal
    :param n_grad_freq: number of frequency channels over which the gradient is computed
    :param n_grad_time: number of frames over which the gradient is computed
    :param n_fft: number of FFT components
    :param win_length: window length
    :param hop_length: hop length
    :param n_std_th: number of standard deviations for the power threshold
    :param prop_decrease: proportion of noise decrease
    :param verbose: print information
    :param visual: plot information
    :return: audio without noise
    """
    # Short-time Fourier transform (STFT) of noise
    if verbose:
        start = time.time()

    noise_stft = librosa.stft(noise_clip, n_fft, hop_length, win_length, window='hann')
    noise_abs = np.abs(noise_stft)
    noise_stft_db = librosa.core.amplitude_to_db(noise_abs, ref=1.0, amin=1e-20, top_db=80.0)

    # Calculate statistics of noise
    mean_noise = np.mean(noise_stft_db, axis=1)
    std_noise = np.std(noise_stft_db, axis=1)
    noise_th = mean_noise + n_std_th * std_noise
    # n_std_th: berapa banyak standar deviasi yang lebih keras dari rata-rata dB kebisingan
    #           (pada setiap tingkat frekuensi) yang dianggap sebagai sinyal

    if verbose:
        print("Noise statistics: mean = %f, std = %f, th = %f" % (mean_noise, std_noise, noise_th))
        print('STFT pada noise:', timedelta(seconds=time.time()-start))
        start = time.time()

    # Short-time Fourier transform (STFT) of audio
    if verbose:
        start = time.time()
    audio_stft = librosa.stft(audio, n_fft, hop_length, win_length, window='hann')
    audio_abs = np.abs(audio_stft)
    audio_stft_db = librosa.core.amplitude_to_db(audio_abs, ref=1.0, amin=1e-20, top_db=80.0)

    if verbose:
        print('STFT pada audio:', timedelta(seconds=time.time()-start))
        start = time.time()

    # Calculate minimum mask
    mask_gain_db = np.min(audio_stft_db)
    if verbose:
        print(noise_th, mask_gain_db)

    # Buat smoothing filter untuk mask pada time dan frequency
    smoothing_filter = np.outer(np.concatenate([np.linspace(0, 1, n_grad_freq + 1, endpoint=False),
                                                np.linspace(1, 0, n_grad_freq + 2)])[1:-1],
                                np.concatenate([np.linspace(0, 1, n_grad_time + 1, endpoint=False),
                                                np.linspace(1, 0, n_grad_time + 2)])[1:-1])

    smoothing_filter = smoothing_filter/np.sum(smoothing_filter)

    # Hitung threshold untuk setiap frequency/time bin
    db_th = np.repeat(np.reshape(noise_th, [1, len(mean_noise)]), np.shape(audio_stft_db)[1], axis=0).T

    # mask jika sinyal diatas threshold
    audio_mask = audio_stft_db < db_th
    if verbose:
        print('Masking:', timedelta(seconds=time.time()-start))
        start = time.time()

    # Apply smoothing filter
    audio_mask = scipy.signal.fftconvolve(audio_mask, smoothing_filter, mode='same')
    audio_mask = audio_mask * prop_decrease
    if verbose:
        print('Mask Convolution Smoothing:', timedelta(seconds=time.time()-start))
        start = time.time()
    
    # Apply mask
    audio_stft_db_masked = audio_stft_db * (1-audio_mask) + np.ones(np.shape(mask_gain_db)) * mask_gain_db * audio_mask  # mask real
    audio_imag_masked = np.imag(audio_stft) * (1 - audio_mask)
    audio_amplitude = librosa.core.db_to_amplitude(audio_stft_db_masked, ref=1.0)
    audio_stft_amplitude = (audio_amplitude * np.sign(audio_stft)) + (1j * audio_imag_masked)

    if verbose: 
        print('Mask application:', timedelta(seconds=time.time()-start))
        start = time.time()

    # recover the signal
    recovered_signal = librosa.istft(audio_stft_amplitude, hop_length, win_length)
    recovered_STFT = librosa.stft(
        recovered_signal, n_fft, hop_length, win_length, window='hann')
    recovered_abs = np.abs(recovered_STFT)
    recovered_spec = librosa.core.amplitude_to_db(
        recovered_abs, ref=1.0, amin=1e-20, top_db=80.0)
    
    if verbose:
        print('Signal recovery:', timedelta(seconds=time.time()-start))
    if visual:
        plot_spectrogram(noise_stft_db, title='Noise')
    if visual:
        plot_statistics_and_filter(mean_noise, std_noise, noise_th, smoothing_filter)
    if visual:
        plot_spectrogram(audio_stft_db, title='Signal')
    if visual:
        plot_spectrogram(audio_mask, title='Mask applied')
    if visual:
        plot_spectrogram(audio_stft_db_masked, title='Masked signal')
    if visual:
        plot_spectrogram(recovered_spec, title='Recovered spectrogram')
    
    return recovered_signal

def noise_reduction(audio, noise_clip, prop_decrease=0.5, verbose=False, visual=False, fft_size=4096, iterations=2):
    output = remove_noise(audio, noise_clip, n_fft=fft_size, win_length=fft_size, prop_decrease=prop_decrease,
                         verbose=False, visual=False)
    iterations = iterations - 1
    while(iterations != 0):
        output = remove_noise(output, noise_clip, n_fft=fft_size, win_length=fft_size, prop_decrease=prop_decrease,
                             verbose=False, visual=False)
        iterations = iterations - 1
    return output


def noise_reduction_final(audio, noise_clip, prop_decrease=0.5, verbose=False, visual=False, fft_size=4096, iterations=2):
    output = remove_noise(audio, noise_clip, n_fft=fft_size, win_length=fft_size, prop_decrease=prop_decrease,
                          n_std_th=0.5, verbose=False, visual=False)
    iterations = iterations - 1
    while(iterations != 0):
        output = remove_noise(output, noise_clip, n_fft=fft_size, win_length=fft_size, prop_decrease=prop_decrease,
                              n_std_th=0.5, verbose=False, visual=False)
        iterations = iterations - 1
    return output
