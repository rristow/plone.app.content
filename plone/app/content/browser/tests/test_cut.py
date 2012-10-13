from plone.app.content.browser.tests.test_doctests import FolderTestCase
import transaction
from plone.locking.interfaces import ILockable

def return_false(self, op=0):
    """peter"""
    return 0


class CutTestCase(FolderTestCase):

    
    def setUp(self):
        super(CutTestCase, self).setUp()
        self.createDocuments(5)

    def test_unauthorized_cut(self):
        self.browser.open("http://nohost/plone/testing-1/object_cut")
        self.assertTrue('id="login_form"' in self.browser.contents)

    def test_cut(self):
        self.loginAsManager()
        self.browser.open("http://nohost/plone/testing-2/object_cut")
        self.assertTrue("Testing \xc3\xa4 2 cut." in self.browser.contents)

    def test_handle_copyerror(self):
        portal = self.portal
        obj = portal['testing-3']
        obj._canCopy = return_false
        self.loginAsManager()
        self.browser.open("http://nohost/plone/testing-3/object_cut")
        self.assertTrue("is not moveable." in self.browser.contents)

    def test_locked(self):
        self.loginAsManager()
        obj = self.portal['testing-4']
        lockable = ILockable(obj)
        lockable.lock()
        transaction.commit()
        self.browser.open("http://nohost/plone/testing-4/object_cut")