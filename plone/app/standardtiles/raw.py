# -*- coding: utf-8 -*-
# this tile will not be registered in the registry
# because it is assumed this will only be used in layouts
# and not added to custom layouts since custom layouts will
# use normal text input

from plone.app.standardtiles import _PMF as _
from plone.supermodel.model import Schema
from plone.tiles import PersistentTile
from Products.CMFCore.utils import getToolByName
from zope import schema


class IRawHTMLTile(Schema):

    content = schema.Text(
        title=_(u"HTML"),
        required=True
    )


class RawHTMLTile(PersistentTile):
    def __call__(self):
        content = self.data.get('content')
        if content:
            # only transform is not rendering for layout editor
            if not self.request.get('_layouteditor'):
                transforms = getToolByName(self.context, 'portal_transforms')
                data = transforms.convertTo('text/x-html-safe', content, mimetype='text/html',
                                            context=self.context)
                content = data.getData()
        else:
            content = u'<p></p>'
        return u"<html><body>%s</body></html>" % content
