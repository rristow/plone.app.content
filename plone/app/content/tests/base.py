import unittest2 as unittest
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing.layers import FunctionalTesting
from plone.testing import z2
from zope.configuration import xmlconfig


class PAContent(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        import plone.app.content
        xmlconfig.file('configure.zcml', plone.app.content,
                       context=configurationContext)
        z2.installProduct(app, 'plone.app.content')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'plone.app.content:default')


PACONTENT_FIXTURE = PAContent()

PACONTENT_FUNCTIONAL_TESTING = \
    FunctionalTesting(bases=(PACONTENT_FIXTURE, ),
                      name="PACONTENT:Functional")


class ContentTestCase(unittest.TestCase):

    layer = PACONTENT_FUNCTIONAL_TESTING


class ContentFunctionalTestCase(unittest.TestCase):

    layer = PACONTENT_FUNCTIONAL_TESTING
