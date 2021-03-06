import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
import soundfile as sf
import sounddevice as sd
import librosa
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import platform
import threading
import concurrent.futures
import change
import utils
import pyaudio
import wave

speakers = ['ANG', 'DIS', 'FEA', 'HAP', 'NEU', 'SAD']


def detail_transform(wav, style):
    return normalize(change.Change(wav, speakers[style]))


def play(wav):
    try:
        CHUNK = 1024
        wf = wave.open(wav, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(CHUNK)
        datas = []
        while len(data) > 0:
            data = wf.readframes(CHUNK)
            datas.append(data)
        for d in datas:
            stream.write(d)
        stream.stop_stream()
        stream.close()
        p.terminate()
    except Exception as e:
        print(e)


def normalize(wav):
    return wav / np.max(np.abs(wav))


class main_window(tk.Tk):
    def button1_on_click(self):
        path = filedialog.askopenfilename(parent=self,
                                          title='打开一个波形文件',
                                          filetypes=[('波形文件', '.wav')])
        if not path:
            return False

        wav, samplerate = sf.read(path)
        self.wav = wav = normalize(librosa.resample(wav, samplerate, 16000))
        self.transformed_wav = None
        sf.write('origin.wav', wav, 16000)

        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2))
        ax = axes.ravel()
        ax[0].plot(np.arange(wav.shape[0]), wav)
        ax[0].set_aspect('auto')
        ax[0].set_title('original wav')
        ax[0].set_xticks([])
        maxabs = np.max(np.abs(wav)) * 1.2
        ax[0].set_ylim([-maxabs, maxabs])
        MFCC = librosa.feature.mfcc(wav, 16000, n_mfcc=36)
        ax[1].imshow(MFCC)
        ax[1].set_aspect('auto')
        ax[1].set_title('original MFCC')
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        ax[1].set_xlabel('frame')
        plt.savefig('origin.png', dpi=100)
        plt.close()
        self.image1 = tk.PhotoImage(file='origin.png')  # 需要对图片保持引用
        self.canvas1.create_image(0, 0, anchor='nw', image=self.image1)

        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2))
        ax = axes.ravel()
        ax[0].set_title('transformed wav')
        ax[0].set_xticks([])
        ax[0].set_yticks([])
        ax[1].set_title('transformed MFCC')
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        plt.savefig('transformed.png', dpi=100)
        plt.close()
        self.image2 = tk.PhotoImage(file='transformed.png')
        self.canvas2.create_image(0, 0, anchor='nw', image=self.image2)
        self.button2_on_click()
        return True

    def button2_on_click(self):
        self.thread_pool_sound.submit(play, 'origin.wav')

    def button3_on_click(self):
        sel_style = self.listbox1.curselection()[0]
        if self.wav is None:
            return
        self.button3.config(state=tk.DISABLED)
        self.button4.config(state=tk.DISABLED)
        self.listbox1.config(state=tk.DISABLED)
        self.thread_pool.submit(self.transform, sel_style)

    def button4_on_click(self):
        self.thread_pool_sound.submit(play, 'transformed.wav')

    def transform(self, style):
        try:
            self.transformed_wav = wav = detail_transform(self.wav, style)
        except Exception as err:
            messagebox.showerror(title='', message=f'出现错误，请重试。错误信息：{err}')
            self.button3.config(state=tk.NORMAL)
            self.button4.config(state=tk.NORMAL)
            self.listbox1.config(state=tk.NORMAL)
        else:
            sf.write('transformed.wav', wav, 16000)
            fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2))
            ax = axes.ravel()
            ax[0].plot(np.arange(wav.shape[0]), wav)
            ax[0].set_aspect('auto')
            ax[0].set_title('transformed wav')
            ax[0].set_xticks([])
            maxabs = np.max(np.abs(wav)) * 1.2
            ax[0].set_ylim([-maxabs, maxabs])
            MFCC = librosa.feature.mfcc(wav, 16000, n_mfcc=36)
            ax[1].imshow(MFCC)
            ax[1].set_aspect('auto')
            ax[1].set_title('transformed MFCC')
            ax[1].set_xticks([])
            ax[1].set_yticks([])
            ax[1].set_xlabel('frame')
            plt.savefig('transformed.png', dpi=100)
            plt.close()
            self.image2 = tk.PhotoImage(file='transformed.png')
            self.canvas2.create_image(0, 0, anchor='nw', image=self.image2)
            self.button4_on_click()

        self.button3.config(state=tk.NORMAL)
        self.button4.config(state=tk.NORMAL)
        self.listbox1.config(state=tk.NORMAL)

    def init_window(self):
        tk.Tk.__init__(self)
        self.tk.call('tk', 'scaling', scale / 75)
        self.title('语音转换')
        self.resizable(0, 0)

    def init_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # (0, 0)
        self.canvas1 = tk.Canvas(self, width=960, height=320)
        self.canvas1.grid(row=0, column=0)
        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2))
        ax = axes.ravel()
        ax[0].set_title('original wav')
        ax[0].set_xticks([])
        ax[0].set_yticks([])
        ax[1].set_title('original MFCC')
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        plt.savefig('origin.png', dpi=100)
        plt.close()
        self.image1 = tk.PhotoImage(file='origin.png')
        self.canvas1.create_image(0, 0, anchor='nw', image=self.image1)

        # (0, 1)
        self.frame1 = tk.Frame(self)
        self.frame1.grid(row=0, column=1, sticky=tk.W+tk.E+tk.N+tk.S)
        self.frame1.grid_columnconfigure(0, weight=1)
        self.frame1.grid_rowconfigure(0, weight=1)
        self.frame1 = tk.Frame(self.frame1)
        self.frame1.grid(row=0, column=0)

        self.button1 = ttk.Button(
            self.frame1, text='打开', command=self.button1_on_click)
        self.button1.pack(pady=8)

        self.button2 = ttk.Button(
            self.frame1, text='播放', command=self.button2_on_click)
        self.button2.pack(pady=8)

        self.button3 = ttk.Button(
            self.frame1, text='转换', command=self.button3_on_click)
        self.button3.pack(pady=8)

        self.button4 = ttk.Button(
            self.frame1, text='播放结果', command=self.button4_on_click)
        self.button4.pack(pady=8)

        # (1, 0)
        self.canvas2 = tk.Canvas(self, width=960, height=320)
        self.canvas2.grid(row=1, column=0)
        fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2))
        ax = axes.ravel()
        ax[0].set_title('transformed wav')
        ax[0].set_xticks([])
        ax[0].set_yticks([])
        ax[1].set_title('transformed MFCC')
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        plt.savefig('transformed.png', dpi=100)
        plt.close()
        self.image2 = tk.PhotoImage(file='transformed.png')
        self.canvas2.create_image(0, 0, anchor='nw', image=self.image2)

        # (1, 1)
        self.frame2 = tk.Frame(self)
        self.frame2.grid(row=1, column=1, sticky=tk.W+tk.E+tk.N+tk.S)
        self.frame2.grid_columnconfigure(0, weight=1)
        self.frame2.grid_rowconfigure(0, weight=1)
        self.frame2 = tk.Frame(self.frame2)
        self.frame2.grid(row=0, column=1, padx=40, pady=8)

        self.label1 = tk.Label(self.frame2, text="转换风格")
        self.label1.pack()

        self.listbox1 = tk.Listbox(self.frame2, selectmode=tk.SINGLE)
        self.listbox1.pack()
        for item in self.styles:
            self.listbox1.insert(tk.END, item)
        self.listbox1.selection_set(0)
        self.listbox1.bind("<Double-Button-1>",
                           lambda _: main.button3_on_click())

    def init_instance(self):
        self.init_window()
        self.init_layout()

    def __init__(self):
        self.declare_variable()
        self.init_instance()

    def declare_variable(self):
        self.wav = None  # 总是假定采样率为 16000 Hz
        self.styles = [f'风格 {speakers[i]}' for i in range(6)]
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.thread_pool_sound = concurrent.futures.ThreadPoolExecutor(
            max_workers=1)

    def __del__(self):
        self.thread_pool.shutdown()
        self.thread_pool_sound.shutdown()

    def message_loop(self):
        return self.mainloop()


if __name__ == '__main__':
    if platform.system() == 'Windows':
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        scale = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    else:
        scale = 100
    mpl.use('agg')
    main = main_window()
    main.message_loop()
