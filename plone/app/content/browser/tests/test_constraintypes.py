import unittest2 as unittest
import transaction
from plone.app.testing import login, setRoles
from plone.app.content.testing import PLONE_APP_CONTENT_FUNCTIONAL_TESTING
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD
from plone.testing.z2 import Browser


class TestConstrainTypes(unittest.TestCase):

    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        portal = self.layer['portal']
        login(portal, TEST_USER_NAME)
        setRoles(portal, TEST_USER_ID, ['Manager'])
        self.folder = portal[portal.invokeFactory(id='folder',
                                                  type_name='Folder')]
        transaction.commit()
        self.browser = Browser(self.layer['app'])

    def _open_form(self):
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (
                               TEST_USER_NAME, TEST_USER_PASSWORD))
        self.browser.open('%s/@@folder_constraintypes_form' %
                          self.folder.absolute_url())

    def test_constraintypes_form_save(self):
        self._open_form()
        cancel_button = self.browser.getControl(name="form.button.Save")
        cancel_button.click()
        self.assertTrue(self.browser.url == self.folder.absolute_url())

    def test_constraintypes_form_cancel(self):
        self._open_form()
        cancel_button = self.browser.getControl(name="form.button.Cancel")
        cancel_button.click()
        self.assertTrue(self.browser.url == self.folder.absolute_url())

    def test_enable_manually(self):
        self._open_form()
        self.browser.getControl(name="constrainTypesMode:int").getControl(
            value='1').click()
        self.browser.getControl(name="form.button.Save").click()
        self._open_form()
        self.assertTrue(self.browser.getControl(name="constrainTypesMode:int")
            .getControl(value='1').selected)

    def test_preferred_types(self):
        self._open_form()
        self.browser.getControl(name="constrainTypesMode:int").getControl(
            value='1').click()
        self.browser.getControl(name="currentPrefer:list").getControl(
            value="Document").click()
        self.browser.getControl(name="form.button.Save").click()
        self._open_form()
        self.assertFalse(self.browser.getControl(name="currentPrefer:list")
            .getControl(value="Document").selected)

    def test_locally_allowed_types(self):
        self._open_form()
        self.browser.getControl(name="constrainTypesMode:int").getControl(
            value='1').click()
        self.browser.getControl(name="currentAllow:list").getControl(
            value="Document").click()
        self.browser.getControl(name="form.button.Save").click()
        self._open_form()
        self.assertTrue(self.browser.getControl(name="currentAllow:list")
            .getControl(value="Document").selected)

    def test_preferred_not_allowed(self):
        self._open_form()
        self.browser.getControl(name="constrainTypesMode:int").getControl(
            value='1').click()
        self.browser.getControl(name="currentPrefer:list").getControl(
            value="Document").click()
        self.browser.getControl(name="currentAllow:list").getControl(
            value="Document").click()
        self.browser.getControl(name="form.button.Save").click()
        self.assertTrue(self.browser.url == '%s/@@folder_constraintypes_form'
                        % self.folder.absolute_url())
        self.assertIn('You cannot have a type as secondary type without having'
                      ' it allowed', self.browser.contents)
