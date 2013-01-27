from plone.app.content.testing import PLONE_APP_CONTENT_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing.z2 import Browser
import transaction
import unittest

text = """I lick my brain in silence
Rather squeeze my head instead
Midget man provoking violence
Listen not to what I said

I said please calm it down
Everything is turning brown

Mutilated lips give a kiss on the wrist
Of the worm like tips of tentacles expanding
In my mind, I'm fine, accepting only fresh brine
You can get another drop of this, yeah you wish...
[repeat]

Laughing lady living lover
Ooo you sassy frassy lassie
Find me the skull of Haile Sellase, I...
Give me shoes so I can tapsy
Tap all over this big world
Take my hand you ugly girl """

props = {'description': 'song by ween',
         'contributors': ['dean ween', 'gene ween'],
         'effective_date': '2004-01-12',
         'expiration_date': '2004-12-12',
         'format': 'text/plain',
         'language': 'english',
         'rights': 'ween music',
         'title': 'mutalitated lips',
         'subject': ['psychedelic', 'pop', '13th floor elevators']}


class TestContentPublishing(unittest.TestCase):
    """ The instant publishing drop down UI.
        !NOTE! CMFDefault.Document overrides setFormat and Format
        so it acts strangely.  This is also hardcoded to work with Document.

        This testcase was written to prevent collector/2914 regressions

        In addition, some more general tests of content_status_modify and
        folder_publish behaviour have been added, since this seems a logical
        place to keep them.
    """
    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder = self.portal[self.portal.invokeFactory('Folder', 'folder')]
        self.portal.acl_users._doAddUser('user1', 'secret', ['Member'], [])
        self.membership = self.portal.portal_membership
        self.workflow = self.portal.portal_workflow
        self.workflow.setDefaultChain('plone_workflow')
        transaction.commit()
        self.setupAuthenticator()

    def setRequestMethod(self, method):
        app = self.layer['app']
        app.REQUEST.set('REQUEST_METHOD', method)
        app.REQUEST.method = method

    def getAuthenticator(self):
        from plone.protect.authenticator import AuthenticatorView
        from re import match
        tag = AuthenticatorView('context', 'request').authenticator()
        pattern = '<input .*name="(\w+)".*value="(\w+)"'
        return match(pattern, tag).groups()

    def setupAuthenticator(self):
        name, token = self.getAuthenticator()
        self.layer['app'].REQUEST.form[name] = token

    def _checkMD(self, obj, **changes):
        """ check the DublinCore Metadata on obj - it must inherit from
        DublinCore """
        if changes:
            _orig_props = {}
            _orig_props.update(props)
            props.update(changes)

        self.assertEqual(obj.Title(), props['title'])
        self.assertEqual(obj.Description(), props['description'])
        self.assertEqual(obj.Subject(), tuple(props['subject']))
        self.assertEqual(obj.ExpirationDate(zone='UTC'),
                         obj._datify(props['expiration_date']).ISO())
        self.assertEqual(obj.EffectiveDate(zone='UTC'),
                         obj._datify(props['effective_date']).ISO())
        self.assertEqual(obj.Format(), props['format'])
        self.assertEqual(obj.Rights(), props['rights'])
        self.assertEqual(obj.Language(), props['language'])
        self.assertEqual(obj.Contributors(), tuple(props['contributors']))

        if changes:
            props.update(_orig_props)

    def testPublishingSubobjects(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.invokeFactory('Folder', id='f1', title='Folder 1')
        self.folder.f1.invokeFactory('Document', id='d2', title='Doc 2')
        self.folder.f1.invokeFactory('Folder', id='f2', title='Folder 2')
        paths = []
        for o in (self.folder.d1, self.folder.f1):
            paths.append('/'.join(o.getPhysicalPath()))

        # folder_publish requires a non-GET request
        self.setRequestMethod('POST')
        self.folder.restrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=paths,
            include_children=True)
        for o in (self.folder.d1, self.folder.f1, self.folder.f1.d2,
                  self.folder.f1.f2):
            self.assertEqual(self.workflow.getInfoFor(o, 'review_state'),
                             'published')

    def testPublishingSubobjectsAndExpireThem(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.invokeFactory('Folder', id='f1', title='Folder 1')
        self.folder.f1.invokeFactory('Document', id='d2', title='Doc 2')
        self.folder.f1.invokeFactory('Folder', id='f2', title='Folder 2')
        paths = []
        for o in (self.folder.d1, self.folder.f1):
            paths.append('/'.join(o.getPhysicalPath()))

        # folder_publish requires a non-GET request
        self.setRequestMethod('POST')
        self.folder.restrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=paths,
            effective_date='1/1/2001',
            expiration_date='1/2/2001',
            include_children=True)
        for o in (self.folder.d1, self.folder.f1, self.folder.f1.d2,
                  self.folder.f1.f2):
            self.assertEqual(self.workflow.getInfoFor(o, 'review_state'),
                             'published')
            self.assertTrue(self.portal.isExpired(o))

    def testPublishingWithoutSubobjects(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.invokeFactory('Folder', id='f1', title='Folder 1')
        self.folder.f1.invokeFactory('Document', id='d2', title='Doc 2')
        self.folder.f1.invokeFactory('Folder', id='f2', title='Folder 2')
        paths = []
        for o in (self.folder.d1, self.folder.f1):
            paths.append('/'.join(o.getPhysicalPath()))

        # folder_publish requires a non-GET request
        self.setRequestMethod('POST')
        self.folder.restrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=paths,
            include_children=False)
        for o in (self.folder.d1, self.folder.f1):
            self.assertEqual(self.workflow.getInfoFor(o, 'review_state'),
                             'published')
        for o in (self.folder.f1.d2, self.folder.f1.f2):
            self.assertEqual(self.workflow.getInfoFor(o, 'review_state'),
                             'visible')

    def testFolderPublishing(self):
        # Make sure object gets published
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='doc1')
        doc1 = self.folder.doc1
        doc_path = '/'.join(doc1.getPhysicalPath())
        self.setRequestMethod('POST')
        self.folder.restrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=[doc_path])
        wtool = self.portal.portal_workflow
        review_state = wtool.getInfoFor(doc1, 'review_state')
        self.assertEqual(review_state, 'published')

    def testCatalogIsUpdatedOnFolderPublish(self):
        # Make sure catalog gets updated
        self.folder.invokeFactory('Document', id='doc1')
        doc1 = self.folder.doc1
        doc_path = '/'.join(doc1.getPhysicalPath())
        self.setRequestMethod('POST')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.unrestrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=[doc_path])
        results = self.portal.portal_catalog(path=doc_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].review_state, 'published')

    def testNoErrorOnBadPaths(self):
        # Ensure we don't fail on a bad path, but transition the good ones
        wtool = self.portal.portal_workflow
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.invokeFactory('Document', 'doc2')
        doc1_path = '/'.join(self.folder.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.doc2.getPhysicalPath())
        paths = [doc1_path, '/garbage/path', doc2_path]
        self.setupAuthenticator()
        self.setRequestMethod('POST')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.unrestrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=paths)
        self.assertEqual(wtool.getInfoFor(self.folder.doc1,
                                          'review_state', None),
                         'published')
        self.assertEqual(wtool.getInfoFor(self.folder.doc2,
                                          'review_state', None),
                         'published')

    def testPublishFailureIsCleanedUp(self):
        # Ensure we don't fail on a bad path, but transition the good ones

        # First we add a failing notifySuccess method to the workflow
        # via a nasty monkey-patch
        from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition

        def notifySuccess(self, obj, action, result):
            raise Exception('Cannot transition')
        orig_notify = DCWorkflowDefinition.notifySuccess
        DCWorkflowDefinition.notifySuccess = notifySuccess

        # now we perform the transition
        self.folder.invokeFactory('Document', 'doc1')
        doc1_path = '/'.join(self.folder.doc1.getPhysicalPath())
        self.setRequestMethod('POST')
        self.setupAuthenticator()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.unrestrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=[doc1_path])
        # because an error was raised during post transition the
        # transaction should have been rolled-back and the state
        # should not have changed
        self.assertNotEqual(self.portal.portal_workflow.getInfoFor(
            self.folder.doc1, 'review_state', None), 'published')

        # undo our nasty patch
        DCWorkflowDefinition.notifySuccess = orig_notify

    def testPublishMultiplePaths(self):
        # Make sure publish works for list of paths
        wtool = self.portal.portal_workflow
        self.folder.invokeFactory('Document', 'doc1')
        self.folder.invokeFactory('Document', 'doc2')
        doc1_path = '/'.join(self.folder.doc1.getPhysicalPath())
        doc2_path = '/'.join(self.folder.doc2.getPhysicalPath())
        self.setRequestMethod('POST')
        self.setupAuthenticator()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.unrestrictedTraverse('@@folder_publish')(
            workflow_action='publish',
            paths=[doc1_path, doc2_path])
        self.assertEqual(
            wtool.getInfoFor(self.folder.doc1, 'review_state', None),
            'published')
        self.assertEqual(
            wtool.getInfoFor(self.folder.doc2, 'review_state', None),
            'published')

    def testGETRaises(self):
        # folder_rename requires a non-GET request and will fail otherwise
        from zExceptions import Forbidden
        self.setRequestMethod('GET')
        with self.assertRaises(Forbidden):
            self.folder.unrestrictedTraverse('@@folder_publish')(
                workflow_action='publish',
                paths=['bogus'])

    def testPublishingNonDefaultPageLeavesFolderAlone(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.d1.restrictedTraverse('@@content_status_modify')('publish')
        self.assertEqual(self.workflow.getInfoFor(self.folder, 'review_state'),
                         'visible')
        self.assertEqual(
            self.workflow.getInfoFor(self.folder.d1, 'review_state'),
            'published')

    def testPublishingDefaultPagePublishesFolder(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.setDefaultPage('d1')
        self.folder.d1.restrictedTraverse('content_status_modify')('publish')
        self.assertEqual(self.workflow.getInfoFor(self.folder, 'review_state'),
                         'published')
        self.assertEqual(
            self.workflow.getInfoFor(self.folder.d1, 'review_state'),
            'published')

    def testPublishingDefaultPageWhenFolderCannotBePublished(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.setDefaultPage('d1')
        # make parent be published already when publishing its default document
        # results in an attempt to do it again
        self.folder.restrictedTraverse('content_status_modify')('publish')
        self.assertEqual(self.workflow.getInfoFor(self.folder, 'review_state'),
                         'published')
        self.folder.d1.restrictedTraverse('content_status_modify')('publish')
        self.assertEqual(self.workflow.getInfoFor(self.folder, 'review_state'),
                         'published')
        self.assertEqual(
            self.workflow.getInfoFor(self.folder.d1, 'review_state'),
            'published')

    # test setting effective/expiration date and isExpired script

    def testIsExpiredWithExplicitExpiredContent(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.d1.restrictedTraverse('content_status_modify')(
            workflow_action='publish',
            effective_date='1/1/2001',
            expiration_date='1/2/2001')
        self.assertTrue(self.portal.isExpired(self.folder.d1))

    def testIsExpiredWithImplicitExpiredContent(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.d1.restrictedTraverse('content_status_modify')(
            workflow_action='publish',
            effective_date='1/1/2001',
            expiration_date='1/2/2001')
        self.assertTrue(self.folder.d1.isExpired())

    def testIsExpiredWithExplicitNonExpiredContent(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.d1.restrictedTraverse('content_status_modify')(
            workflow_action='publish')
        self.assertFalse(self.portal.isExpired(self.folder.d1))

    def testIsExpiredWithImplicitNonExpiredContent(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='d1', title='Doc 1')
        self.folder.d1.restrictedTraverse('content_status_modify')(
            workflow_action='publish')
        self.assertFalse(self.folder.d1.isExpired())


class TestContentStatusHistoryForm(unittest.TestCase):
    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.workflow = portal.portal_workflow
        self.workflow.setDefaultChain('plone_workflow')
        self.uf = self.portal.acl_users
        self.uf.userFolderAddUser('manager', 'secret', ['Manager'], [])
        self.folder = portal[portal.invokeFactory(id='folder',
                                                  type_name='Folder')]
        # Create some content
        self.folder.invokeFactory(id='doc1',
                                  type_name="Document")
        self.folder.invokeFactory(id='doc2',
                                  type_name="Document")
        transaction.commit()
        self.browser = Browser(self.layer['app'])

    def _login(self):
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (
                               'manager', 'secret'))

    def test_content_status_modify_no_transition(self):
        self._login()
        self.browser.open('%s/content_status_modify' %
                          self.folder.absolute_url())

        # There should be a status message
        self.assertIn('portalMessage error',
                      self.browser.contents)

    def test_content_status_history_single_item(self):
        self._login()
        self.browser.open('%s/content_status_history' %
                          self.folder.doc1.absolute_url())

        self.browser.getControl(name='workflow_action').getControl(
            value='publish').click()

        self.browser.getControl(name='form.button.Publish').click()

        self.assertEqual(
            self.workflow.getInfoFor(self.folder.doc1, 'review_state'),
            'published')
        self.assertIn('Item state changed.', self.browser.contents)

    def test_content_status_history_multible_items(self):
        self._login()
        self.browser.open('%s/folder_contents' %
                          self.folder.absolute_url())

        # Go to folder_contents, choose both items and go ahead to
        # the content_status_history
        self.browser.getControl(name='paths:list').getControl(
            value='/plone/folder/doc1').click()
        self.browser.getControl(name='paths:list').getControl(
            value='/plone/folder/doc2').click()
        self.browser.getControl(name='content_status_history:method').click()
        self.assertIn(
            'form.button.FolderPublish', self.browser.contents)

        # First unselect both items and try to submit
        self.browser.getControl(name='paths:list').getControl(
            value='/plone/folder/doc1').click()
        self.browser.getControl(name='paths:list').getControl(
            value='/plone/folder/doc2').click()

        self.browser.getControl(name='workflow_action').getControl(
            value='publish').click()

        self.browser.getControl(name='form.button.FolderPublish').click()

        self.assertEqual(
            self.workflow.getInfoFor(self.folder.doc1, 'review_state'),
            'visible')
        self.assertEqual(
            self.workflow.getInfoFor(self.folder.doc2, 'review_state'),
            'visible')

        # Status error message
        self.assertIn('Please correct the indicated errors.',
                      self.browser.contents)
        # Field error message
        self.assertIn('You must select content to change.',
                      self.browser.contents)

        # Second submit form with items
        self.browser.getControl(name='form.button.FolderPublish').click()

        self.assertEqual(
            self.workflow.getInfoFor(self.folder.doc1, 'review_state'),
            'published')
        self.assertEqual(
            self.workflow.getInfoFor(self.folder.doc2, 'review_state'),
            'published')

        # Status info message
        self.assertIn('Item state changed.', self.browser.contents)
