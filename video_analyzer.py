import os
import sys

# Get the absolute path to the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the video_libraries directory
libraries_dir = os.path.join(script_dir, "video_libraries")

# Append the libraries directory to the Python path
sys.path.append(libraries_dir)

# Import necessary modules and libraries
import os
import sys
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.filechooser import FileChooserIconView
import moviepy.editor as mp
import speech_recognition as sr
import openai
import threading
from kivy.core.window import Window

# Set the OpenAI API key
api_key = os.environ.get('OPENAI_API_KEY', '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')
openai.api_key = api_key

# Define the UploadScreen class
class UploadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.file_chooser = FileChooserIconView(path='.', filters=['*.mp4'])
        self.layout.add_widget(self.file_chooser)
        confirm_btn = Button(text='Confirm', size_hint=(0.2, 0.1), pos_hint={'center_x': 0.5, 'y': 0.1})
        confirm_btn.bind(on_press=self.confirm_button_pressed)
        self.layout.add_widget(confirm_btn)
        self.add_widget(self.layout)
        Window.size = (900, 800)

    def confirm_button_pressed(self, instance):
        selected_file = self.file_chooser.selection and self.file_chooser.selection[0]
        if selected_file:
            print("Selected video:", selected_file)
            self.manager.get_screen('main').selected_file = selected_file
        self.parent.current = 'main'

# Define the MainScreen class
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.selected_file = None
        self.original_text = ""
        self.label = Label(text='Hello, Kivy!', pos_hint={'x': 0.4, 'y': 0.8})
        self.layout.add_widget(self.label)
        self.text_input = TextInput(text='', size_hint=(0.9, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.6})
        self.layout.add_widget(self.text_input)

        # Create and configure the Transcribe button
        transcribe_btn = Button(size_hint=(None, None), size=(110, 110), pos_hint={'center_x': 0.8, 'y': 0.08},
                                background_normal="/mnt/storage1/video_analyzer/video_analyzer/video/desktop-2-128.png",
                                background_down="/mnt/storage1/video_analyzer/video_analyzer/video/desktop-2-128.png")
        transcribe_btn.bind(on_press=self.transcribe_button_pressed)
        self.layout.add_widget(transcribe_btn)

        # Create and configure the "Analyze" label
        analyze_label = Label(text="Analyze", color=(1, 1, 1, 1), size_hint=(None, None),
                              pos_hint={'center_x': 0.8, 'y': 0.00009}, font_name='Roboto', font_size=24)
        self.layout.add_widget(analyze_label)

        # Create and configure the Upload button
        upload_btn = Button(size_hint=(None, None), size=(110, 110), pos_hint={'center_x': 0.2, 'y': 0.08},
                            background_normal="/mnt/storage1/video_analyzer/video_analyzer/video/arrow-up-6-128.png",
                            background_down="/mnt/storage1/video_analyzer/video_analyzer/video/arrow-up-6-128.png")
        upload_btn.bind(on_press=self.upload_button_pressed)

        # Create and configure the "Upload a Video" label
        upload_label = Label(text="Upload a Video", color=(1, 1, 1, 1), size_hint=(None, None),
                             pos_hint={'center_x': 0.2, 'y': 0.00009}, font_name='Roboto', font_size=24)
        self.layout.add_widget(upload_label)

        self.layout.add_widget(upload_btn)
        self.add_widget(self.layout)

    def transcribe_and_interpret(self):
        if not self.selected_file:
            print("No file selected.")
            return
        video_clip = mp.VideoFileClip(self.selected_file)
        audio_clip = video_clip.audio
        audio_file_path = "temp_audio.wav"
        audio_clip.write_audiofile(audio_file_path)
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)
            try:
                transcription = recognizer.recognize_sphinx(audio_data)
                print("Transcription: " + transcription)

                response = openai.ChatCompletion.create(
                    model="gpt-4-0314",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Please provide a detailed breakdown or analysis of the following "
                                                    "video: " + transcription
                                                    + transcription}
                    ]
                )

                interpretation = response['choices'][0]['message']['content']
                print("ChatGPT Interpretation:", interpretation)

                Clock.schedule_once(lambda dt: self.update_text_input(interpretation), 0)
            except sr.UnknownValueError:
                print("Could not understand audio")
        audio_clip.close()
        video_clip.close()

    def update_text_input(self, interpretation):
        self.text_input.text = "Interpretation:\n" + interpretation
        self.text_input.font_size = 20

    def transcribe_button_pressed(self, instance):
        self.original_text = self.text_input.text
        self.text_input.text = "The video is being analyzed. Please wait."
        self.text_input.font_size = 20
        threading.Thread(target=self.transcribe_and_interpret).start()

    def upload_button_pressed(self, instance):
        self.parent.current = 'upload'

# Define the main application class
class MyApp(App):
    def build(self):
        self.title = 'Video Analyzer'
        screen_manager = ScreenManager(transition=NoTransition())
        main_screen = MainScreen(name='main')
        upload_screen = UploadScreen(name='upload')
        screen_manager.add_widget(main_screen)
        screen_manager.add_widget(upload_screen)
        return screen_manager

# Entry point of the application
if __name__ == '__main__':
    MyApp().run()
