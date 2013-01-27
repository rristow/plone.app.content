from zope.testing import doctest
import transaction
import unittest
from unittest import TestSuite
from plone.app.content.testing import PLONE_APP_CONTENT_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Testing.ZopeTestCase import FunctionalDocFileSuite


OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


class FolderTestCase(unittest.TestCase):
    """base test case with convenience methods for all control panel tests"""

    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        from plone.testing.z2 import Browser
        self.browser = Browser(self.layer['app'])
        self.portal = self.layer['portal']
        self.uf = self.portal.acl_users
        self.uf.userFolderAddUser('root', 'secret', ['Manager'], [])

    def createDocuments(self, amount):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        for i in xrange(1, amount + 1):
            self.portal.invokeFactory('Document', 'testing-%d' % i)
            document = getattr(self.portal, 'testing-%d' % i)
            document.setTitle(unicode('Testing \xc3\xa4 %d' % i, 'utf-8'))
            document.setExcludeFromNav(True)
            document.reindexObject()
        transaction.commit()

    def createFolder(self, id='new-folder'):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory(id=id, type_name='Folder')
        folder = getattr(self.portal, id)
        folder.setTitle('New Folder')
        folder.setExcludeFromNav(True)
        folder.reindexObject()
        transaction.commit()

    def loginAsManager(self):
        self.browser.open('http://nohost/plone/')
        self.browser.getLink('Log in').click()
        self.browser.getControl('Login Name').value = 'root'
        self.browser.getControl('Password').value = 'secret'
        self.browser.getControl('Log in').click()


def test_suite():
    tests = ['foldercontents.txt', 'change_ownership.txt']
    suite = TestSuite()
    for test in tests:
        suite.addTest(FunctionalDocFileSuite(
            test,
            optionflags=OPTIONFLAGS,
            package="plone.app.content.browser.tests",
            test_class=FolderTestCase))
    return suite
