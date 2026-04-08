import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import proxy_forge
import configparser

class ProxyForgeApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        # Here we can add Kivy widgets as necessary
        layout.add_widget(Label(text='ProxyForge Initialized'))
        return layout

    def on_start(self):
        # Initialization logic for proxy_forge
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        # You can add further initialization with proxy_forge
        proxy_forge.initialize(self.config)

if __name__ == '__main__':
    ProxyForgeApp().run()