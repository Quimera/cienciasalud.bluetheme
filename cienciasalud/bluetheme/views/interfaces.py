from zope.interface import Interface


class IMediaWidget(Interface):

    def generate_widget(self):
        """Generate the video widget based in configuration"""
