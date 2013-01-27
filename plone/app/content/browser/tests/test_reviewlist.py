import transaction
import unittest

from Products.CMFCore.utils import getToolByName
from plone.app.content.testing import PLONE_APP_CONTENT_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.testing.z2 import Browser


class ReviewListTestCase(unittest.TestCase):
    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.uf = self.portal.acl_users
        self.uf.userFolderAddUser('reviewer', 'secret', ['Reviewer'], [])
        self.browser = Browser(self.layer['app'])
        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.wftool.setDefaultChain('plone_workflow')
        transaction.commit()

    def createDocument(self, id, title, description):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory(id=id, type_name='Document')
        doc = getattr(self.portal, id)
        doc.setTitle(title)
        doc.setDescription(description)
        # we don't want it in the navigation
        doc.setExcludeFromNav(True)
        doc.reindexObject()
        return doc

    def submitToReview(self, obj):
        '''call the workflow action 'submit' for an object'''
        self.wftool.doActionFor(obj, 'submit')

    def test_unauthenticated(self):
        '''
        unauthenticated users do not have the necessary permissions to view
        the review list
        '''
        self.browser.open('http://nohost/plone/full_review_list')
        self.assertTrue('Login Name' in self.browser.contents)

    def test_authenticated(self):
        '''
        unauthenticated users do not have the necessary permissions to view
        the review list
        '''
        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        self.browser.open('http://nohost/plone/full_review_list')
        self.assertTrue('Full review list:' in self.browser.contents)

    def test_with_content(self):
        '''
        unauthenticated users do not have the necessary permissions to view
        the review list
        '''
        doc = self.createDocument('testdoc', 'Test Document', 'Test Description')
        self.wftool.doActionFor(doc, 'submit')
        transaction.commit()

        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        self.browser.open('http://nohost/plone/full_review_list')
        self.assertTrue('Full review list:' in self.browser.contents)
        # test if the table with review items contains an entry for testdoc
        self.assertTrue('value="/plone/testdoc"' in self.browser.contents)
