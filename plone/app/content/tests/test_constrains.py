# -*- coding: utf-8 -*-
import unittest2 as unittest

from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFCore.utils import getToolByName
from zope.interface.exceptions import Invalid

from plone.app.content.testing import (
    PLONE_APP_CONTENT_INTEGRATION_TESTING,
    PLONE_APP_CONTENT_FUNCTIONAL_TESTING
)

from plone.app.content.browser.constraintypes import IConstrainForm

from plone.app.content.browser import constraintypes

from plone.app.testing import TEST_USER_ID, setRoles


class ConstrainsIntegrationTest(unittest.TestCase):

    layer = PLONE_APP_CONTENT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['ACTUAL_URL'] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']

        self.folder.invokeFactory('Folder', 'inner_folder')
        self.inner_folder = self.folder['inner_folder']

        self.types_tool = getToolByName(self.portal, 'portal_types')
        folder_type = self.types_tool.getTypeInfo(self.folder)
        self.default_types = [t for t in self.types_tool.listTypeInfo() if
                              t.isConstructionAllowed(self.folder)
                              and folder_type.allowType(t.getId())]
        assert len(self.default_types) > 3
        self.types_id_subset = [t.getId() for t in self.default_types][:2]

    def test_formschemainvariants(self):
        class Data(object):
            allow = []
            allow_2nd_step = []
        bad = Data()
        bad.allow = []
        bad.allow_2nd_step = ['1']
        good = Data()
        good.allow = ['1']
        good.allow_2nd_step = []
        self.assertTrue(IConstrainForm.validateInvariants(good) is None)
        self.assertRaises(Invalid, IConstrainForm.validateInvariants, bad)

    def test_formContentAdapterConstraintypes(self):
        adapter = IConstrainForm(ISelectableConstrainTypes(self.folder))
        self.assertEquals(0, adapter.constrain_types_mode)
        adapter.constrain_types_mode = 1
        self.assertEquals(1, adapter.constrain_types_mode)

    def test_formContentAdaptercurrentprefer(self):
        aspect = ISelectableConstrainTypes(self.folder)
        adapter = IConstrainForm(aspect)

        aspect.setConstrainTypesMode(constraintypes.ENABLED)
        adapter.allow = ["Document", "Folder"]
        adapter.allow_2nd_step = ["Document"]


        self.assertEquals(["Document", "Folder"],
                          list(aspect.getLocallyAllowedTypes()))
        self.assertEquals(["Folder"],
                          list(aspect.getImmediatelyAddableTypes()))

        self.assertEquals(["Document", "Folder"], list(adapter.allow))
        self.assertEquals(["Document"], list(adapter.allow_2nd_step))

        adapter.allow = ["Document"]
        adapter.allow_2nd_step = ["Document", "Folder"]

        self.assertEquals(["Document"], list(aspect.getLocallyAllowedTypes()))
        self.assertEquals([], list(aspect.getImmediatelyAddableTypes()))


class FolderConstrainViewFunctionalText(unittest.TestCase):

    layer = PLONE_APP_CONTENT_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal_url = self.portal.absolute_url()
        self.portal.invokeFactory('Folder', id='folder', title='My Folder')
        self.folder = self.portal.folder
        self.folder_url = self.folder.absolute_url()
        import transaction
        transaction.commit()
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_folder_view(self):
        self.browser.open(self.folder_url + '/view')
        self.assertTrue('My Folder' in self.browser.contents)
        self.assertTrue('Restrictions' in self.browser.contents)

    def test_folder_restrictions_view(self):
        self.browser.open(self.folder_url + '/folder_constraintypes_form')
        self.assertTrue("Restrict what types" in self.browser.contents)
        self.assertTrue("// Custom form constraints for constrain form" in
                        self.browser.contents)
        self.assertTrue("allow_form" in self.browser.contents)

    def test_form_save_restrictions(self):
        self.browser.open(self.folder_url)
        self.browser.getLink('Restrictions').click()
        ctrl = lambda name: self.browser.getControl(name=name)
        self.browser.getControl("Type restrictions").value = ['1']
        ctrl("form.widgets.allow:list").value = ["Document", "Folder"]
        ctrl("form.widgets.allow_2nd_step:list").value = ["Document"]
        self.browser.getControl("Save").click()
        aspect = ISelectableConstrainTypes(self.folder)
        self.assertEquals(1, aspect.getConstrainTypesMode())
        self.assertEquals(["Document", "Folder"],
                          list(aspect.getLocallyAllowedTypes()))
        self.assertEquals(["Folder"],
                          list(aspect.getImmediatelyAddableTypes()))

    def test_form_bad_save(self):
        aspect = ISelectableConstrainTypes(self.folder)
        constraint_before = aspect.getConstrainTypesMode()
        assert constraint_before != 1, ("Default constraint should not be 1. "
                                        "Test is outdated.")

        self.browser.open(self.folder_url)
        self.browser.getLink('Restrictions').click()
        ctrl = lambda name: self.browser.getControl(name=name)
        self.browser.getControl("Type restrictions").value = ['1']
        ctrl("form.widgets.allow:list").value = ["Document"]
        ctrl("form.widgets.allow_2nd_step:list").value = ["Document", "Folder"]
        self.browser.getControl("Save").click()
        self.assertEquals(constraint_before, aspect.getConstrainTypesMode())
        self.assertTrue('Error' in self.browser.contents)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
