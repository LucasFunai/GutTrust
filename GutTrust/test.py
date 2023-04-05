from kivy.app import App
from kivy.base import Builder
from kivy.uix.boxlayout import BoxLayout


Builder.load_string("""
<MainWindow>:
    StackLayout:
        id : aa
        orientation: 'lr-tb'

        canvas:
            Color:
                rgba: 1,1,1,1
            Rectangle:
                pos: 0, self.height*0.9
                size: self.width, self.height*0.1

        Image:
            id: im
            size_hint_y: 0.1
            source: 'Images\login\cptbanner.jpg'
            allow_stretch: True
            keep_ratio: True
""")

class MainWindow(BoxLayout):
    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)

class MyApp(App):
    def build(self):
        return MainWindow()

if __name__ == '__main__':
    MyApp().run()