from zope import schema
from zope.interface import implements
from zope.publisher.interfaces import NotFound
from zope.publisher.interfaces import IPublishTraverse

from plone.directives import form as directivesform

from plone.tiles import PersistentTile
from plone.tiles.interfaces import ITile

from plone.namedfile.utils import set_headers, stream_data
from plone.namedfile.field import NamedImage


class IImageTile(directivesform.Schema):

    image = NamedImage(title=u"Please upload an image", required=True)
    altText = schema.TextLine(title=u"Alternative text", required=False)


class ImageTile(PersistentTile):
    """Image tile.
    
    This is a persistent tile which stores an image and optionally alt
    text. When rendered, the tile will output an <img /> tag like::
    
        <img src="http://.../@@plone.app.standardtiles.image/tile-id/@@download/filename.gif" />
    
    The tile is a publish traversal view, so it will stream the file data
    if the correct filename (matching the uploaded filename), is given in
    the traversal subpath (filename.gif in the example above). Note that the
    ``id`` query string parameter is still required for the tile to be able to
    access its persistent data.
    """

    def __call__(self):
        # Not for production use - this should be in a template!
        image = self.data.get('image', None)
        if image is not None:
            altText = self.data.get('altText', '').replace('"', '\"')
            filename = image.filename
            imageURL = "%s/@@download/%s" % (self.url, filename,)
            return '<html><body><img src="%s" alt="%s" /></body></html>' % (imageURL, altText)
        else:
            return '<html><body><em>No image set</em></body></html>'

class ImageTileDownload(object):
    """Implementation of the @@download view on the image tile.
    
    This is a view onto the ImageTile tile view.
    """
    
    implements(IPublishTraverse)
    filename = None
    
    def publishTraverse(self, request, name):
        if self.filename is None:
            self.filename = name
            return self
        raise NotFound(name)
    
    def __call__(self):
        """Render the file to the browser
        """
        
        image = self.context.data.get('image', None)
        if image is None:
            raise NotFound(self, self.filename, self.request)
        
        if not self.filename:
            self.filename = getattr(image, 'filename', '')
        
        set_headers(image, self.request.response, filename=self.filename)
        return stream_data(image)
