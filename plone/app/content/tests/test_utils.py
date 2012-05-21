from zope.component import getMultiAdapter
from AccessControl import Unauthorized
from plone.app.content.testing import PLONE_APP_CONTENT_INTEGRATION_TESTING
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME
from plone.app.testing import setRoles, login
import unittest2 as unittest
from zope.component import getUtility
from plone.keyring.interfaces import IKeyManager
import hmac
import transaction

try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


class Base(unittest.TestCase):
    layer = PLONE_APP_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)

    def setAuth(self):
        manager = getUtility(IKeyManager)
        secret = manager.secret()
        self.request.set('REQUEST_METHOD', 'POST')
        self.request.method = 'POST'
        token = hmac.new(secret, TEST_USER_NAME, sha).hexdigest()
        self.request.form['_authenticator'] = token


class TestDelete(Base):

    def testObjectDeleteFailsWithoutProtection(self):
        self.portal.invokeFactory('Folder', 'folder')
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_delete")
        self.assertRaises(Unauthorized, view)

    def testObjectDelete(self):
        self.portal.invokeFactory('Folder', 'folder')
        folder = self.portal.folder
        folder.invokeFactory('Document', id='doc')
        doc = folder.doc
        self.setAuth()
        view = getMultiAdapter((doc, self.request), name="object_delete")
        view()
        assert 'doc' not in folder


class TestCutCopyAndPaste(Base):

    def testObjectCopyFailsWithoutProtection(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_copy")
        self.assertRaises(Unauthorized, view)

    def testObjectPasteFailsWithoutProtection(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_paste")
        self.assertRaises(Unauthorized, view)

    def testObjectCutFailsWithoutProtection(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_cut")
        self.assertRaises(Unauthorized, view)

    def testCopyObjectDoesNotThrowUnauthorized(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_copy")()

    def testCutObjectDoesNotThrowUnauthorized(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_cut")()

    def testPasteObjectDoesNotThrowUnauthorized(self):
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        folder = self.portal.folder
        #first cut
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_cut")()
        getMultiAdapter((self.portal, self.request), name="object_paste")()

    def testCopyPaste(self):
        self.portal.invokeFactory('Document', 'doc')
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        doc = self.portal.doc
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((doc, self.request), name="object_copy")()
        getMultiAdapter((folder, self.request), name="object_paste")()
        assert 'doc' in folder
        assert 'doc' in self.portal

    def testCutPaste(self):
        self.portal.invokeFactory('Document', 'doc')
        self.portal.invokeFactory('Folder', 'folder')
        transaction.savepoint()
        doc = self.portal.doc
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((doc, self.request), name="object_cut")()
        getMultiAdapter((folder, self.request), name="object_paste")()
        assert 'doc' in folder
        assert 'doc' not in self.portal
