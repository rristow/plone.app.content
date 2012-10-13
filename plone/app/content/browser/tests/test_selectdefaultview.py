# -*- coding: utf-8 -*-
import unittest
from transaction import commit

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.ploneview import Plone

from Products.CMFPlone.tests import dummy
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

class SelectDefaultViewTestCase(FunctionalTestCase):

    def afterSetUp(self):
        super(SelectDefaultViewTestCase, self).afterSetUp()

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
        commit()
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
        commit()
        return doc

    def _create_structure(self):
        folder = self._createFolder()
        self.wftool.doActionFor(folder, 'submit')


        doc = self._createDocument(folder)
        self.wftool.doActionFor(doc, 'submit')
        return folder

    def _invalidateRequestMemoizations(self):
        try:
            del self.app.REQUEST.__annotations__
        except AttributeError:
            pass

    def testIsDefaultPageInFolder(self):
        folder = self._create_structure()

        self.browser.addHeader('Authorization',
                               'Basic %s:%s' % ('reviewer', 'secret'))
        view = Plone(folder[DOCUMENT['id']], self.app.REQUEST)
        self.assertFalse(view.isDefaultPageInFolder())
        self.assertTrue(folder.canSelectDefaultPage())
        #folder.saveDefaultPage('test')

        self.browser.open(folder.absolute_url()+'/@@select_default_page')
        cancel_button = self.browser.getControl(name="form.button.Save")
        cancel_button.click()

        ## re-create the view, because the old value is cached
        self._invalidateRequestMemoizations()
        view = Plone(folder[DOCUMENT['id']], self.app.REQUEST)
        self.assertTrue(view.isDefaultPageInFolder())
        
    def testIsFolderOrFolderDefaultPage(self):
        folder = self._create_structure()
        # an actual folder whould return true
        view = Plone(folder, self.app.REQUEST)
        self.assertTrue(view.isFolderOrFolderDefaultPage())
        # But not a document
        self._invalidateRequestMemoizations()
        view = Plone(folder[DOCUMENT['id']], self.app.REQUEST)
        self.assertFalse(view.isFolderOrFolderDefaultPage())
        # Unless we make it the default view
        #folder.saveDefaultPage('test')
        self.browser.open(folder.absolute_url()+'/@@select_default_page')
        cancel_button = self.browser.getControl(name="form.button.Save")
        cancel_button.click()
        
        self._invalidateRequestMemoizations()
        view = Plone(folder[DOCUMENT['id']], self.app.REQUEST)
        self.assertTrue(view.isFolderOrFolderDefaultPage())
        # And if we have a non-structural folder it should not be true
        f = dummy.NonStructuralFolder('ns_folder')
        folder._setObject('ns_folder', f)
        self._invalidateRequestMemoizations()
        view = Plone(folder.ns_folder, self.app.REQUEST)
        self.assertFalse(view.isFolderOrFolderDefaultPage())
        
    def testIsPortalOrPortalDefaultPage(self):
        folder = self._create_structure()
        # an actual folder whould return true
        view = Plone(self.portal, self.app.REQUEST)
        self.assertTrue(view.isPortalOrPortalDefaultPage())
        # But not a document
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'portal_test',
                                  title='Test default page')
        self._invalidateRequestMemoizations()
        view = Plone(self.portal.portal_test, self.app.REQUEST)
        self.assertFalse(view.isPortalOrPortalDefaultPage())
        # Unless we make it the default view
        #self.portal.saveDefaultPage('portal_test')
        self.browser.open(folder.absolute_url()+'/@@select_default_page')
        cancel_button = self.browser.getControl(name="form.button.Save")
        cancel_button.click()
        
        self._invalidateRequestMemoizations()
        view = Plone(self.portal.portal_test, self.app.REQUEST)
        self.assertTrue(view.isPortalOrPortalDefaultPage())
        
    def testGetCurrentFolder(self):
        folder = self._create_structure()
        # If context is a folder, then the folder is returned
        view = Plone(folder, self.app.REQUEST)
        self.assertEqual(view.getCurrentFolder(), folder)

        # If context is not a folder, then the parent is returned
        # A bit crude ... we need to make sure our memos don't stick in the
        # tests
        self._invalidateRequestMemoizations()
        view = Plone(folder[DOCUMENT['id']], self.app.REQUEST)
        self.assertEqual(view.getCurrentFolder(), folder)

        # The real container is returned regardless of context
        self._invalidateRequestMemoizations()
        view = Plone(folder[DOCUMENT['id']].__of__(self.portal), self.app.REQUEST)
        self.assertEqual(view.getCurrentFolder(), folder)

        # A non-structural folder does not count as a folder`
        f = dummy.NonStructuralFolder('ns_folder')
        folder._setObject('ns_folder', f)
        self._invalidateRequestMemoizations()
        view = Plone(folder.ns_folder, self.app.REQUEST)
        self.assertEqual(view.getCurrentFolder(), folder)

        # And even a structural folder that is used as a default page
        # returns its parent
        folder.saveDefaultPage('ns_folder')
        self._invalidateRequestMemoizations()
        view = Plone(folder.ns_folder, self.app.REQUEST)
        self.assertEqual(view.getCurrentFolder(), folder)
