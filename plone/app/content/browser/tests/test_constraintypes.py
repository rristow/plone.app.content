# -*- coding: utf-8 -*-
import unittest
from transaction import commit

from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite

from Products.Five.testbrowser import Browser

setupPloneSite()


class TestConstrainTypes(FunctionalTestCase):

    def afterSetUp(self):
        super(TestConstrainTypes, self).afterSetUp()
        portal = self.portal
        self.setRoles(['Manager',])
        self.uf = self.portal.acl_users
        self.uf.userFolderAddUser('manager', 'secret', ['Manager'], [])
        self.folder = portal[portal.invokeFactory(id='folder',
                                                  type_name='Folder')]
        commit()
        self.browser = Browser()

    def _open_form(self):
        self.browser.addHeader('Authorization', 'Basic %s:%s' % (
                               'manager', 'secret'))
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
