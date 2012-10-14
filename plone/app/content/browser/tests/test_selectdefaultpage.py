# -*- coding: utf-8 -*-
import unittest

from Products.CMFCore.utils import getToolByName

from Products.PloneTestCase.PloneTestCase import FunctionalTestCase
from Products.PloneTestCase.PloneTestCase import setupPloneSite

from Products.Five.testbrowser import Browser

setupPloneSite()


FOLDER = { 'id': 'testfolder',
           'title': 'Test Folder',
           'description': 'Test Folder Description'}

DOCUMENT = { 'id': 'testdoc',
             'title': 'Test Document',
             'description': 'Test Document Description'}


class SelectDefaultPageTestCase(FunctionalTestCase):
    """
    """

    def afterSetUp(self):
        super(SelectDefaultPageTestCase, self).afterSetUp()

        self.uf = self.portal.acl_users
        self.uf.userFolderAddUser('reviewer', 'secret', ['Reviewer'], [])
        self.browser = Browser()
        self.wftool = getToolByName(self.portal, 'portal_workflow')

    def _createFolder(self):
        self.setRoles(['Manager',])
        self.portal.invokeFactory(id=FOLDER['id'], type_name='Folder')
        folder = getattr(self.portal, FOLDER['id'])
        folder.setTitle(FOLDER['title'])
        folder.setDescription(FOLDER['description'])
        folder.reindexObject()
        # we don't want it in the navigation
        folder.setExcludeFromNav(True)
        return folder

    def _createDocument(self, context):
        self.setRoles(['Manager',])
        context.invokeFactory(id=DOCUMENT['id'], type_name='Document')
        doc = getattr(context, DOCUMENT['id'])
        doc.setTitle(DOCUMENT['title'])
        doc.setDescription(DOCUMENT['description'])
        doc.reindexObject()
        # we don't want it in the navigation
        doc.setExcludeFromNav(True)
        return doc

    def _create_structure(self):
        folder = self._createFolder()
        self.wftool.doActionFor(folder, 'submit')

        doc = self._createDocument(folder)
        self.wftool.doActionFor(doc, 'submit')
        return folder

    def test_select_default_page_view(self):
        '''
        Check that the select_default_page view is shown
        '''
        folder = self._create_structure()

        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        self.browser.open('%s/@@select_default_page' % folder.absolute_url())

        self.assertTrue('Select default page' in self.browser.contents)
        self.assertTrue('id="testdoc"' in self.browser.contents)

    def test_default_page_action_cancel(self):
        '''
        check that the select_default_page view cancel button brings you
        back to the folder view
        '''
        folder = self._create_structure()

        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        self.browser.open('%s/@@select_default_page' % folder.absolute_url())

        cancel_button = self.browser.getControl(name="form.button.Cancel")
        cancel_button.click()

        self.assertTrue(self.browser.url == folder.absolute_url())
        self.assertTrue(FOLDER['description'] in self.browser.contents)

    def test_default_page_action_save(self):
        '''
        check that the select_default_page view submit button brings you back
        to the folder view but seeing the document
        '''
        folder = self._create_structure()

        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        self.browser.open('%s/@@select_default_page' % folder.absolute_url())

        submit_button = self.browser.getControl(name="form.button.Save")
        submit_button.click()

        self.assertTrue(self.browser.url == folder.absolute_url())
        self.assertTrue(DOCUMENT['description'] in self.browser.contents)
        self.assertFalse(FOLDER['description'] in self.browser.contents)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SelectDefaultPageTestCase))
    return suite
