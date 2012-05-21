from zope import component
from zExceptions import Forbidden
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.interface import directlyProvides
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
from Products.CMFPlone.tests.dummy import ICantBeDeleted, disallow_delete_handler
from OFS.SimpleItem import Item

try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


class Base(unittest.TestCase):
    layer = PLONE_APP_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.app = self.layer['app']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, TEST_USER_NAME)
        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal.folder

    def setAuth(self):
        manager = getUtility(IKeyManager)
        secret = manager.secret()
        self.request.set('REQUEST_METHOD', 'POST')
        self.request.method = 'POST'
        token = hmac.new(secret, TEST_USER_NAME, sha).hexdigest()
        self.request.form['_authenticator'] = token

    def setRequestMethod(self, method):
        self.request.set('REQUEST_METHOD', method)
        self.request.method = method


class TestDelete(Base):

    def testObjectDeleteFailsWithoutProtection(self):
        view = getMultiAdapter((self.folder, self.request),
            name="object_delete")
        self.assertRaises(Unauthorized, view)

    def testObjectDelete(self):
        self.folder.invokeFactory('Document', id='doc')
        doc = self.folder.doc
        self.setAuth()
        view = getMultiAdapter((doc, self.request), name="object_delete")
        view()
        assert 'doc' not in self.folder


class TestCutCopyAndPaste(Base):

    def testObjectCopyFailsWithoutProtection(self):
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_copy")
        self.assertRaises(Unauthorized, view)

    def testObjectPasteFailsWithoutProtection(self):
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_paste")
        self.assertRaises(Unauthorized, view)

    def testObjectCutFailsWithoutProtection(self):
        transaction.savepoint()
        folder = self.portal.folder
        view = getMultiAdapter((folder, self.request), name="object_cut")
        self.assertRaises(Unauthorized, view)

    def testCopyObjectDoesNotThrowUnauthorized(self):
        transaction.savepoint()
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_copy")()

    def testCutObjectDoesNotThrowUnauthorized(self):
        transaction.savepoint()
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_cut")()

    def testPasteObjectDoesNotThrowUnauthorized(self):
        transaction.savepoint()
        folder = self.portal.folder
        #first cut
        self.setAuth()
        getMultiAdapter((folder, self.request), name="object_cut")()
        getMultiAdapter((self.portal, self.request), name="object_paste")()

    def testCopyPaste(self):
        self.portal.invokeFactory('Document', 'doc')
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
        transaction.savepoint()
        doc = self.portal.doc
        folder = self.portal.folder
        self.setAuth()
        getMultiAdapter((doc, self.request), name="object_cut")()
        getMultiAdapter((folder, self.request), name="object_paste")()
        assert 'doc' in folder
        assert 'doc' not in self.portal


class TestFolderRename(Base):
    # Tests for folder_rename and folder_rename_form

    def setUp(self):
        super(TestFolderRename, self).setUp()
        self.catalog = self.portal.portal_catalog
        self.folder.invokeFactory('Folder', id='foo')
        self.folder.invokeFactory('Folder', id='bar')
        self.folder.foo.invokeFactory('Document', id='doc1')
        self.folder.bar.invokeFactory('Document', id='doc2')
        # folder_rename requires a non-GET request
        self.setAuth()

    def testTitleIsUpdatedOnTitleChange(self):
        # Make sure our title is updated on the object
        title = 'Test Doc - Snooze!'
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
                        name="folder_rename")
        view([doc_path], ['doc1'], [title])
        obj = self.folder.foo.doc1
        self.assertEqual(obj.Title(), title)

    def testCatalogTitleIsUpdatedOnFolderTitleChange(self):
        # Make sure our title is updated in the catalog
        title = 'Test Doc - Snooze!'
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
                        name="folder_rename")
        view([doc_path], ['doc1'], [title])
        results = self.catalog(Title='Snooze')
        self.failUnless(results)
        for result in results:
            self.assertEqual(result.Title, title)
            self.assertEqual(result.id, 'doc1')

    def testTitleAndIdAreUpdatedOnFolderRename(self):
        # Make sure rename updates both title and id
        title = 'Test Folder - Snooze!'
        transaction.savepoint(optimistic=True)  # make rename work
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
                        name="folder_rename")
        view([doc_path], ['baz'], [title])
        self.assertEqual(getattr(self.folder.foo, 'doc1', None), None)
        self.failUnless(getattr(self.folder.foo, 'baz', None) is not None)
        self.assertEqual(self.folder.foo.baz.Title(), title)

    def testCatalogTitleAndIdAreUpdatedOnFolderRename(self):
        # Make sure catalog updates title on rename
        title = 'Test Folder - Snooze!'
        transaction.savepoint(optimistic=True)  # make rename work
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
                               name="folder_rename")
        view(paths=[doc_path], new_ids=['baz'], new_titles=[title])
        results = self.catalog(Title='Snooze')
        self.failUnless(results)
        for result in results:
            self.assertEqual(result.Title, title)
            self.assertEqual(result.id, 'baz')

    def testUpdateMultiplePaths(self):
        # Ensure this works for multiple paths
        title = 'Test Folder - Snooze!'
        transaction.savepoint(optimistic=True)  # make rename work
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.bar.doc2.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
                               name="folder_rename")
        view(paths=[doc1_path, doc2_path],
            new_ids=['baz', 'blah'], new_titles=[title, title])
        self.assertEqual(getattr(self.folder.foo, 'doc1', None), None)
        self.assertEqual(getattr(self.folder.bar, 'doc2', None), None)
        self.failUnless(getattr(self.folder.foo, 'baz', None) is not None)
        self.failUnless(getattr(self.folder.bar, 'blah', None) is not None)
        self.assertEqual(self.folder.foo.baz.Title(), title)
        self.assertEqual(self.folder.bar.blah.Title(), title)

    def testNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path
        self.app.REQUEST.set('paths', ['/garbage/path'])
        self.folder.folder_rename_form()

    def testGETRaises(self):
        # folder_rename requires a non-GET request and will fail otherwise
        self.setRequestMethod('GET')
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        view = getMultiAdapter((self.folder, self.request),
            name="folder_rename")
        self.assertRaises(Forbidden, view, [doc1_path], ['bar'], ['Baz'])

    def testGetObjectsFromPathList(self):
        doc1_path = unicode('/'.join(self.folder.foo.doc1.getPhysicalPath()))
        doc2_path = unicode('/'.join(self.folder.bar.doc2.getPhysicalPath()))
        self.assertEqual(len(self.folder.getObjectsFromPathList(
            [doc1_path, doc2_path])), 2)


class TestFolderDelete(Base):
    # Tests for folder_delete.py

    def setUp(self):
        super(TestFolderDelete, self).setUp()
        self.catalog = self.portal.portal_catalog
        self.folder.invokeFactory('Folder', id='foo')
        self.folder.invokeFactory('Folder', id='bar')
        self.folder.foo.invokeFactory('Document', id='doc1')
        self.folder.bar.invokeFactory('Document', id='doc2')
        self.setAuth()

    def beforeTearDown(self):
        # unregister our deletion event subscriber
        component.getSiteManager().unregisterHandler(disallow_delete_handler,
                                                     [ICantBeDeleted,
                                                      IObjectRemovedEvent])

    def testFolderDeletion(self):
        # Make sure object gets deleted
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        self.app.REQUEST.set('paths', [doc_path])
        view = getMultiAdapter((self.folder, self.request),
            name="folder_delete")
        view()
        self.assertEqual(getattr(self.folder.foo, 'doc1', None), None)

    def testCatalogIsUpdatedOnFolderDelete(self):
        # Make sure catalog gets updated
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        self.request.set('paths', [doc_path])
        view = getMultiAdapter((self.folder, self.request),
            name="folder_delete")
        view()
        results = self.catalog(path=doc_path)
        self.failIf(results)

    def testDeleteMultiplePaths(self):
        # Make sure deletion works for list of paths
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.bar.doc2.getPhysicalPath())
        self.request.set('paths', [doc1_path, doc2_path])
        view = getMultiAdapter((self.folder, self.request),
            name="folder_delete")
        view()
        self.assertEqual(getattr(self.folder.foo, 'doc1', None), None)
        self.assertEqual(getattr(self.folder.bar, 'doc2', None), None)

    def testNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path
        self.request.set('paths', ['/garbage/path'])
        getMultiAdapter((self.folder, self.request), name="folder_delete")()

    def testGETRaisesUnauthorized(self):
        # folder_delete requires a non-GET request and will fail otherwise
        self.setRequestMethod('GET')
        view = getMultiAdapter((self.folder, self.request),
            name="folder_delete")
        self.assertRaises(Forbidden, view)


class TestFolderPublish(Base):
    # Tests for folder_publish and content_status_history and
    # content_status_modify

    def setUp(self):
        super(TestFolderPublish, self).setUp()
        self.catalog = self.portal.portal_catalog
        self.wtool = self.portal.portal_workflow
        self.folder.invokeFactory('Folder', id='foo')
        self.folder.invokeFactory('Folder', id='bar')
        self.folder.foo.invokeFactory('Document', id='doc1')
        self.folder.bar.invokeFactory('Document', id='doc2')
        self.portal.acl_users._doAddUser('reviewer', 'secret',
                                         ['Reviewer'], [])
        # folder_publish requires a non-GET request
        self.setRequestMethod('POST')

    def testFolderPublishing(self):
        # Make sure object gets published
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        setRoles(self.portal, TEST_USER_ID, ['Reviewer'])
        self.setAuth()
        self.folder.folder_publish(workflow_action='publish', paths=[doc_path])
        self.assertEqual(self.wtool.getInfoFor(
            self.folder.foo.doc1, 'review_state', None), 'published')

    def testCatalogIsUpdatedOnFolderPublish(self):
        # Make sure catalog gets updated
        doc_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        setRoles(self.portal, TEST_USER_ID, ['Reviewer'])
        self.setAuth()
        self.folder.folder_publish(workflow_action='publish', paths=[doc_path])
        results = self.catalog(path=doc_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].review_state, 'published')

    def testPublishMultiplePaths(self):
        # Make sure publish works for list of paths
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.bar.doc2.getPhysicalPath())
        setRoles(self.portal, TEST_USER_ID, ['Reviewer'])
        self.setAuth()
        self.folder.folder_publish('publish', paths=[doc1_path, doc2_path])
        self.assertEqual(self.wtool.getInfoFor(
            self.folder.foo.doc1, 'review_state', None), 'published')
        self.assertEqual(self.wtool.getInfoFor(
            self.folder.bar.doc2, 'review_state', None), 'published')

    def testNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path, but transition the good ones
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.bar.doc2.getPhysicalPath())
        paths = [doc1_path, '/garbage/path', doc2_path]
        setRoles(self.portal, TEST_USER_ID, ['Reviewer'])
        self.setAuth()
        self.folder.folder_publish('publish', paths=paths)
        self.assertEqual(self.wtool.getInfoFor(
            self.folder.foo.doc1, 'review_state', None), 'published')
        self.assertEqual(self.wtool.getInfoFor(self.folder.bar.doc2,
            'review_state', None), 'published')

    def testPublishFailureIsCleanedUp(self):
        # Ensure we don't fail on a bad path, but transition the good ones

        # First we add a failing notifySuccess method to the workflow
        # via a nasty monkey-patch
        from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
        def notifySuccess(self, obj, action, result):
            raise Exception, 'Cannot transition'
        orig_notify = DCWorkflowDefinition.notifySuccess
        DCWorkflowDefinition.notifySuccess = notifySuccess

        # now we perform the transition
        doc1_path = '/'.join(self.folder.foo.doc1.getPhysicalPath())
        setRoles(self.portal, TEST_USER_ID, ['Reviewer'])
        self.setAuth()
        self.folder.folder_publish('publish', paths=[doc1_path])
        # because an error was raised during post transition the
        # transaction should have been rolled-back and the state
        # should not have changed
        self.failIfEqual(self.wtool.getInfoFor(self.folder.foo.doc1,
                                               'review_state', None),
                         'published')

        # undo our nasty patch
        DCWorkflowDefinition.notifySuccess = orig_notify

    def testGETRaises(self):
        # folder_rename requires a non-GET request and will fail otherwise
        self.setRequestMethod('GET')
        self.assertRaises(Forbidden, self.folder.folder_publish,
                          'publish', paths=['bogus'])


class TestFolderCutCopy(Base):
    # Tests for folder_cut.py and folder_copy.py

    def testCutNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path
        self.request.set('paths', ['/garbage/path'])
        self.setAuth()
        view = getMultiAdapter((self.folder, self.request), name="folder_cut")
        view()

    def testCopyNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path
        self.request.set('paths', ['/garbage/path'])
        self.setAuth()
        view = getMultiAdapter((self.folder, self.request), name="folder_copy")
        view()
