# -*- coding: utf-8 -*-

from zope.component import getMultiAdapter

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from collective.cover.tiles.list import ListTile, IListTile

#from openmultimedia.contenttypes.content.video import IVideo


class INitfSecundary(IListTile):
    pass


class NitfSecundary(ListTile):

    index = ViewPageTemplateFile("templates/nitf_secundary.pt")

    is_configurable = True
    limit = 6

    def accepted_ct(self):
        valid_ct = ['collective.nitf.content', 'News Item', ]
        return valid_ct

    #def _get_brains(self, obj, object_provides=None):
    #    """ Return a list of brains inside the NITF object.
    #    """
    #    catalog = getToolByName(self.context, 'portal_catalog')
    #    path = '/'.join(obj.getPhysicalPath())
    #    brains = catalog(object_provides=object_provides, path=path,
    #                     sort_on='getObjPositionInParent')

    #    return brains

    #def get_images(self, obj):
    #    """ Return a list of image brains inside the NITF object.
    #    """
    #    return self._get_brains(obj, IATImage.__identifier__)

    #def get_videos(self, obj):
    #    """ Return a list of image brains inside the NITF object.
    #    """
    #    return self._get_brains(obj, IVideo.__identifier__)

    def has_images(self, obj):
        """ Return the number of images inside the NITF object.
        """
        return len(self.get_images(obj))

    def has_videos(self, obj):
        """ Return the number of images inside the NITF object.
        """
        return len(self.get_videos(obj))

    def getImage(self, obj):
        images = self.get_images(obj)
        if len(images) > 0:
            return images[0].getObject()
        return None

    def getVideo(self, obj):
        videos = self.get_videos(obj)
        if len(videos) > 0:
            return videos[0].getObject()
        return None

    def imageCaption(self, obj):
        image = self.getImage(obj)
        if image is not None:
            return image.Description()

    def media_data(self, obj):
        media = {'type': None, 'media': None, 'item': None}
        if obj:
            nitf_view = getMultiAdapter((obj, self.request),
                                        name=u'view')
            media_list = nitf_view.get_media()
            if media_list:
                media['media'] = media_list[0].getObject()
                media['type'] = nitf_view.media_type(media['media'])
            media['item'] = obj

        return media

    def tag(self, obj, **kwargs):
        # tag original implementation returns object title in both, alt and
        # title attributes
        image = self.getImage(obj)
        if image is not None:
            return image.tag(**kwargs)
