import unittest
from plone.app.testing import PLONE_INTEGRATION_TESTING


class AddingTests(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_adding_acquisition(self):
        from Acquisition import aq_get

        self.portal = self.layer['portal']
        adding = self.portal.unrestrictedTraverse('+')
        # Check explicit Acquisition
        template = aq_get(adding, 'main_template')
        self.assertTrue(template)
        # Check implicit Acquisition, unfortunately the CMF skins machinery
        # depends on this
        template = getattr(adding, 'main_template')
        self.assertTrue(template)
        # Check traversal
        self.assertTrue(self.portal.unrestrictedTraverse('+/main_template'))
