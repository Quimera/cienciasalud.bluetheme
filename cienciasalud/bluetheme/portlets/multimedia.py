# -*- coding:utf-8 -*-
from time import time

from zope import schema
from zope.formlib import form

from zope.interface import implements
from zope.component import getUtility

from plone.memoize import ram
from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.ATContentTypes.interfaces import IATImage
from Products.CMFCore.utils import getToolByName

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from openmultimedia.api.interfaces import IVideoAPI
from cienciasalud.bluetheme import _


class IMultimediaPortlet(IPortletDataProvider):
    """A portlet
    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    videos_url = schema.TextLine(
        title=_(u'Videos url'),
        required=False,
    )

    limit = schema.TextLine(
        title=_(u'Limit'),
        required=False,
    )

    show_date = schema.Bool(
        title=_(u'Show Dates'),
        default=True,
        required=False,
    )


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(IMultimediaPortlet)

    show_dates = True
    pretty_date = True

    def __init__(self, videos_url='', limit=4, show_date=True, **kwargs):
        self.show_date = show_date
        self.videos_url = videos_url
        self.limit = limit

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"Multimedia Portlet (Gallery and video")


def cache_key_simple(func, var):
    #let's memoize for 5 minutes or if any value of the tile is modified.
    timeout = time() // (60 * 5)
    return (timeout,)


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('multimedia.pt')

    LIMIT = 4

    def get_video_url(self):
        return self.data.videos_url

    def get_limit(self):
        limit = self.LIMIT
        if self.data.limit:
            limit = self.data.limit
        return int(limit)

    @ram.cache(cache_key_simple)
    def results(self):
        limit = self.get_limit()
        url = self.get_video_url()
        video_api = getUtility(IVideoAPI)
        if not url:
            url = video_api.get_basic_clip_list(offset=0, limit=limit)
            url = "%s&tipo_contenido=video-externo" % url
        content_json = video_api.get_json(url)
        return content_json[:limit]

    def view_date(self, item):
        date = item.Date()
        if item.effective_date:
            date = item.effective_date
        else:
            date = item.creation_date
        return date.strftime("%d.%m.%Y")

    def show_dates(self):
        return self.data.show_date


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(IMultimediaPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(IMultimediaPortlet)
