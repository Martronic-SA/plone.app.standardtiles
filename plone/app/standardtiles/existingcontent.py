# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from zope.component import provideAdapter
from zope.interface import Invalid
from plone.app.blocks import utils
from plone.app.blocks.tiles import renderTiles
from plone.app.standardtiles import PloneMessageFactory as _
from plone.app.uuid.utils import uuidToObject
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.memoize.view import memoize
from plone.supermodel import model
from plone.tiles import Tile
from plone.uuid.interfaces import IUUID
from repoze.xmliter.utils import getHTMLSerializer
from zope import schema
from zope.browser.interfaces import IBrowserView
from z3c.form import validator


class CatalogSource(CatalogSourceBase):
    """ExistingContentTile specific catalog source to allow targeted widget
    """


class IExistingContentTile(model.Schema):

    content_uid = schema.Choice(
        title=_(u"Select an existing content"),
        required=True,
        source=CatalogSource(),
    )


class SameContentValidator(validator.SimpleFieldValidator):
    def validate(self, content_uid):
        super(SameContentValidator, self).validate(content_uid)
        context = aq_parent(self.context)  # default context is tile data
        if content_uid and IUUID(context, None) == content_uid:
            raise Invalid("You can not select the same content as "
                          "the page you are currently on.")


# Register validator
validator.WidgetValidatorDiscriminators(
    SameContentValidator, field=IExistingContentTile['content_uid'])
provideAdapter(SameContentValidator)


class ExistingContentTile(Tile):
    """Existing content tile
    """

    @property
    @memoize
    def content_context(self):
        uuid = self.data.get('content_uid')
        if uuid != IUUID(self.context, None):
            item = uuidToObject(uuid)
            if item is not None:
                return item
        return None

    @property
    @memoize
    def default_view(self):
        context = self.content_context
        if context is not None:
            item_layout = context.getLayout()
            default_view = context.restrictedTraverse(item_layout)
            return default_view
        return None

    @property
    def item_macros(self):
        default_view = self.default_view
        if default_view and IBrowserView.providedBy(default_view):
            # IBrowserView
            if getattr(default_view, 'index', None):
                return default_view.index.macros
        elif default_view:
            # FSPageTemplate
            return default_view.macros
        return None

    @property
    def item_panels(self):
        default_view = self.default_view
        html = default_view()
        if isinstance(html, unicode):
            html = html.encode('utf-8')
        serializer = getHTMLSerializer([html], pretty_print=False,
                                       encoding='utf-8')
        panels = dict(
            (node.attrib['data-panel'], node)
            for node in utils.panelXPath(serializer.tree)
        )
        if panels:
            request = self.request.clone()
            request.URL = self.content_context.absolute_url() + '/'
            try:
                renderTiles(request, serializer.tree)
            except RuntimeError:  # maximum recursion depth exceeded
                return []
            clear = '<div style="clear: both;"></div>'
            return [''.join([serializer.serializer(child)
                             for child in node.getchildren()])
                    for name, node in panels.items()] + [clear]
        return []
