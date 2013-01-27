import unittest
from plone.app.content.testing import PLONE_APP_CONTENT_INTEGRATION_TESTING


class TestBaseContent(unittest.TestCase):

    layer = PLONE_APP_CONTENT_INTEGRATION_TESTING

    def _makeContainer(self):
        from zope.interface import implements, Interface
        from zope import schema
        from zope.component.factory import Factory
        from plone.app.content.container import Container

        class IMyContainer(Interface):
            title = schema.TextLine(title=u"My title")
            description = schema.TextLine(title=u"My other title")

        class MyContainer(Container):
            implements(IMyContainer)
            portal_type = "My container"
            title = u""
            description = u""

        containerFactory = Factory(MyContainer)
        container = containerFactory("my-container")
        container.title = "A sample container"
        newid = self.layer['portal']._setObject(container.id, container)
        container = getattr(self.layer['portal'], newid)
        return container

    def _makeItem(self):
        from zope.interface import implements, Interface
        from zope import schema
        from zope.component.factory import Factory
        from plone.app.content.item import Item

        class IMyType(Interface):
            title = schema.TextLine(title=u"My title")
            description = schema.TextLine(title=u"My other title")

        class MyType(Item):
            implements(IMyType)
            portal_type = "My type"
            title = u""
            description = u""

        itemFactory = Factory(MyType)
        item = itemFactory('my-item')
        item.title = 'A non-folderish item'
        return item

    def test_container_contentish(self):
        container = self._makeContainer()
        from Products.CMFCore.interfaces import IContentish
        self.assertTrue(IContentish.providedBy(container))

    def test_container_folderish(self):
        container = self._makeContainer()
        from Products.CMFCore.interfaces import IFolderish
        self.assertTrue(IFolderish.providedBy(container))
        self.assertTrue(container.isPrincipiaFolderish)

    def test_item_contentish(self):
        item = self._makeItem()
        from Products.CMFCore.interfaces import IContentish
        self.assertTrue(IContentish.providedBy(item))

    def test_item_not_folderish(self):
        item = self._makeItem()
        from Products.CMFCore.interfaces import IFolderish
        self.assertFalse(IFolderish.providedBy(item))
        self.assertFalse(item.isPrincipiaFolderish)

    def test_add_item_to_container__setObject(self):
        container = self._makeContainer()
        item = self._makeItem()

        container._setObject('my-item', item)
        self.assertTrue('my-item' in container)
        self.assertTrue('my-item' in container.objectIds())

    def test_delete_item_from_container(self):
        container = self._makeContainer()
        item = self._makeItem()

        container['my-item'] = item
        del container['my-item']
        self.assertFalse('my-item' in container)

    def test_catalog(self):
        container = self._makeContainer()
        item = self._makeItem()

        container['my-item'] = item
        item = container['my-item']
        self.assertTrue('my-item' in container)
        self.assertTrue('my-item' in container.objectIds())

        from Products.CMFCore.utils import getToolByName
        catalog = getToolByName(self.layer['portal'], 'portal_catalog')
        self.assertEqual(
            [b.Title for b in catalog(getId='my-container')],
            ['A sample container']
        )
        self.assertEqual(
            [b.Title for b in catalog(getId='my-item')],
            ['A non-folderish item']
        )

        from zope.lifecycleevent import ObjectModifiedEvent
        from zope.event import notify

        container.title = "Updated title"
        item.title = "Also updated title"

        notify(ObjectModifiedEvent(container))
        notify(ObjectModifiedEvent(item))

        self.assertEqual(
            [b.Title for b in catalog(getId='my-container')],
            ['Updated title']
        )
        self.assertEqual(
            [b.Title for b in catalog(getId='my-item')],
            ['Also updated title']
        )
