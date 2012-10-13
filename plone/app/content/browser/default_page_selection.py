# -*- coding: utf-8 -*-
from zope.publisher.browser import BrowserView
from Products.CMFPlone import PloneMessageFactory as _


class DefaultPageSelectionView(BrowserView):

    def __call__(self):
        url = self.context.absolute_url()

        if 'form.button.Save' in self.request.keys():
            putils = self.context.plone_utils

            if not 'objectId' in self.request.keys():
                putils.addPortalMessage(_(u'Please select an item to use.'),
                                        'error')
                url += "/@@select_default_page"
            else:
                objectId = self.request['objectId']

                if not objectId in self.context.objectIds():
                    message = _(u'There is no object with short name ${name} '
                                 'in this folder.',
                                mapping={u'name': objectId})

                    putils.addPortalMessage(message, 'error')
                    url += "/@@select_default_page"
                else:
                    self.context.setDefaultPage(objectId)
                    putils.addPortalMessage(_(u'View changed.'))

        return self.request.response.redirect(url)
