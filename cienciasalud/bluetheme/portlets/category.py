# -*- coding:utf-8 -*-
from AccessControl import getSecurityManager

from zope.formlib import form
from zope.interface import implements
from zope import schema
from zope.component import getMultiAdapter

from plone.memoize.instance import memoize

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.vocabularies.catalog import SearchableTextSourceBinder

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from cienciasalud.bluetheme import _


class ICategoryPortlet(IPortletDataProvider):
    """A portlet
    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """

    target_collection = schema.List(title=u"People  names",
                                    value_type=schema.Choice(
                                        title=_(u"Target collection"),
                                        description=_(u"Find the collection which provides the items to list"),
                                        required=True,
                                        source=SearchableTextSourceBinder(
                                            {'portal_type': ('Topic', 'Collection')},
                                            default_query='path:')
                                    ),
                                    required=True)

    limit = schema.Int(
        title=_(u"Limit"),
        description=_(u"Specify the maximum number of items to show in the "
                      u"portlet. Leave this blank to show all items."),
        required=False)


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ICategoryPortlet)

    target_collection = None
    limit = None

    def __init__(self, target_collection=None, limit=None, **kwargs):
        self.target_collection = target_collection
        self.limit = limit

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"Category Portlet")


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    @memoize
    def results(self):
        return self._standard_results()

    @memoize
    def collections(self):
        collections_path = self.data.target_collection
        if not collections_path:
            return None

        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u'plone_portal_state')
        portal = portal_state.portal()

        result = []
        for collection_path in collections_path:

            if collection_path.startswith('/'):
                collection_path = collection_path[1:]

            if not collection_path:
                continue

            if isinstance(collection_path, unicode):
                # restrictedTraverse accepts only strings
                collection_path = str(collection_path)

            collection = portal.unrestrictedTraverse(collection_path, default=None)
            if collection is not None:
                sm = getSecurityManager()
                if not sm.checkPermission('View', collection):
                    collection = None
                result.append(collection)
        return result

    def _standard_results(self):
        collections_result = []
        results = []
        collections = self.collections()
        for collection in collections:
            if collection is not None:
                limit = self.data.limit
                if limit and limit > 0:
                    # pass on batching hints to the catalog
                    results = collection.queryCatalog(batch=True, b_size=limit)
                    results = results._sequence
                else:
                    results = collection.queryCatalog()
                if limit and limit > 0:
                    results = results[:limit]
            collections_result.append((collection, results))
        return collections_result

    render = ViewPageTemplateFile('category.pt')


class AddForm(base.AddForm):
    """Portlet add form.

    This is registered in configure.zcml. The form_fields variable tells
    zope.formlib which fields to display. The create() method actually
    constructs the assignment that is being added.
    """
    form_fields = form.Fields(ICategoryPortlet)

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):
    """Portlet edit form.

    This is registered with configure.zcml. The form_fields variable tells
    zope.formlib which fields to display.
    """
    form_fields = form.Fields(ICategoryPortlet)

