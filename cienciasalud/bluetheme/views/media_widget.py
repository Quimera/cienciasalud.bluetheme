from zope.interface import implements

from Products.Five import BrowserView
from cienciasalud.bluetheme.views.interfaces import IMediaWidget
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from uuid import uuid1


class MediaWidget(BrowserView):
    implements(IMediaWidget)

    video_template = ViewPageTemplateFile('templates/media_widget.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request

        conf = {
            'width': '300',
            'height': '200',
            'id': str(uuid1()),
            'style': 0,
            'channel': 'cienciasalud'
        }

        self.default_conf = conf
        for i in conf:
            if i in self.request:
                self.default_conf[i] = self.request[i]

    def generate_widget(self, **kwargs):
        """Generate the video widget based in configuration"""

        if kwargs:
            conf = dict(self.default_conf.items() + kwargs.items())
        else:
            conf = self.default_conf
        self.conf = conf

        return self.video_template()

    def js_code(self):
        code = """
        $(document).ready(function() {
        OMPlayer.setup({id: '%s', slug: '%s',
         width: %s, height: %s, style: %s, channel:'%s'});
        });
        """ % (self.conf['id'],
               self.conf['slug'], self.conf['width'], self.conf['height'],
               self.conf['style'], self.conf['channel'])
        return code

    def js_code_playlist(self):
        code = """
        $(document).ready(function() {
            var player = $('#%(id)s');
            container = player.parent();
            var width = %(width)s;
            if(container.width() > width) {
                width = container.width();
            }
            player.omplayer({slugs: %(slugs)s, width: width, height: %(height)s,
                style: %(style)s, channel:'%(channel)s'});
            function playListResize() {
                var newSize = container.width();
                if (player.width() > newSize && newSize > 310 && newSize < %(width)s) {
                    player.width(newSize).omplayer('resize', newSize, %(height)s);
                } else  if (player.width() < %(width)s && newSize > 310 && newSize < %(width)s) {
                    player.width(newSize).omplayer('resize', newSize, %(height)s);
                }
            }
            $(window).resize(playListResize);
            playListResize();
        });
        """ % dict(id=self.conf['id'], width=self.conf['width'],
                   slugs=self.conf['slugs'], height=self.conf['height'],
                   style=self.conf['style'], channel=self.conf['channel'])
        return code
