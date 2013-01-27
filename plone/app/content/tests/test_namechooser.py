import unittest2 as unittest
from plone.app.content.testing import PLONE_APP_CONTENT_INTEGRATION_TESTING
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import setRoles, login
from plone.app.content.namechooser import ATTEMPTS
from zope.container.interfaces import INameChooser


class NameChooserTest(unittest.TestCase):
    layer = PLONE_APP_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def test_100_or_more_unique_ids(self):
        # add the same item 110 times. the first 100 items should be numbered.
        # after that it should use datetime to generate the id
        self.portal.invokeFactory("Folder", 'holder')
        holder = self.portal.get('holder')
        
        title = "A Small Document"
        # create the first object, which will have no suffix
        holder.invokeFactory("Document", id='a-small-document')

        chooser = INameChooser(holder)
         
        for i in range(1, ATTEMPTS + 1):
            id = chooser.chooseName(title, holder)
            if i <= ATTEMPTS: # first addition has no suffix
                self.assertEqual("a-small-document-%s"%i, id)
            else:
                self.assertNotEqual("a-small-document-%s"%i, id)

            holder.invokeFactory("Document", id)
            item = holder.get(id)

    def test_integration(self):
        """
        plone.app.content provides a namechooser for IFolderish objects that
        can pick a normalized name based on the object's id, title, portal
        type or class, and can provide uniqueness.
        """

        # Let's create some dummy content.

        from plone.app.content import container, item
        from zope.interface import implements, Interface, alsoProvides
        from zope import schema
    
        class IMyContainer(Interface):
            title = schema.TextLine(title=u"My title")
            description = schema.TextLine(title=u"My other title")

        class MyContainer(container.Container):
            implements(IMyContainer)
            portal_type = "My container"
            title = IMyContainer['title']
            description = IMyContainer['description']

        class IMyType(Interface):
            title = schema.TextLine(title=u"My title")
            description = schema.TextLine(title=u"My other title")
    
        class MyType(item.Item):
            implements(IMyType)
            portal_type = "My portal type"
            title = IMyType['title']
            description = IMyType['description']

        container = MyContainer("my-container")
        self.layer['portal']['my-container'] = container
        container = self.layer['portal']['my-container']

        # Then wire up the name chooser (this is normally done in this
        # package's configure.zcml file).
        from zope.component import adapts, provideAdapter, provideUtility
        from Products.CMFCore.interfaces import IFolderish
        from plone.app.content.namechooser import NormalizingNameChooser
        provideAdapter(adapts=(IFolderish,), factory=NormalizingNameChooser)

        # We also need to wire up some adapters from plone.i18n that are used
        # to normalise URLs.

        from zope.publisher.interfaces.http import IHTTPRequest
        from plone.i18n.normalizer import urlnormalizer
        from plone.i18n.normalizer.adapters import UserPreferredURLNormalizer
        provideUtility(component=urlnormalizer)
        provideAdapter(factory=UserPreferredURLNormalizer,
                       adapts=(IHTTPRequest,))

        """
        Choosing names based on id
        ---------------------------

        By default, the namechooser will choose a name based on the id
        attribute of an object, if it has one.
        """

        from zope.container.interfaces import INameChooser
        chooser = INameChooser(container)

        item = MyType("my-item")
        self.assertEqual(item.id, 'my-item')
    
        name = chooser.chooseName(None, item)
        self.assertEqual(name, 'my-item')
        self.assertTrue(chooser.checkName(name, object))

        """
        If we add it to the container and try again, we'll get a name that's
        made unique.
        """

        container[name] = item

        item = MyType("my-item")  # a distinct object, but with the same id
        name = chooser.chooseName(None, item)
        self.assertEqual(name, 'my-item-1')
        self.assertTrue(chooser.checkName(name, object))

        """
        The uniqueness applies also if we pass a name in, in which case it will
        not be obtained from the id (or portal type or class or title)
        """

        item.id = "another-id"
        self.assertEqual(chooser.chooseName("my-item", item), 'my-item-1')

        """When a filename is used as an id, the extension is preserved."""

        item = MyType("file.txt")
        name = chooser.chooseName(None, item)
        self.assertEqual(name, 'file.txt')
        self.assertTrue(chooser.checkName(name, object))

        container[name] = item
        item = MyType("file.txt")  # a distinct object, but with the same id
        name = chooser.chooseName(None, item)
        self.assertEqual(name, 'file-1.txt')
        self.assertTrue(chooser.checkName(name, object))

        """
        If the chooser is used with a container that implements the
        IObjectManager interface from OFS, the checkValidId method
        of that interface will be used to check for validity of the
        chosen name. This catches various edge cases.
        """

        from OFS.ObjectManager import ObjectManager
        om = ObjectManager()
        om.title = 'foo'
        alsoProvides(om, IFolderish)
        chooser2 = INameChooser(om)
        self.assertEqual(chooser2.chooseName('title', item), 'title-1')

        """
        Choosing names based on type
        ----------------------------

        If we did not have an id, the namechooser would use the portal_type,
        falling back on the class name.
        """

        delattr(item, 'id')
        self.assertEqual(chooser.chooseName(None, item), 'my-portal-type')
    
        delattr(MyType, 'portal_type')
        self.assertEqual(chooser.chooseName(None, item), 'mytype')

        """
        Title-based name chooser
        ------------------------

        An object can also gain a name based on its title. To do so, the object
        must implement or be adaptable to INameFromTitle.
        """

        from plone.app.content.interfaces import INameFromTitle
    
        class TitleAdapter(object):
            implements(INameFromTitle)
            adapts(IMyType)

            def __init__(self, context):
                self.context = context

            @property
            def title(self):
                return self.context.title
        provideAdapter(TitleAdapter)
    
        item = MyType("some-id")
        item.title = u"My funky item"
        self.assertEqual(chooser.chooseName(None, item), 'my-funky-item')
