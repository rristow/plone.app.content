from zope.publisher.browser import BrowserView
from Products.CMFPlone import PloneMessageFactory as _
from Products.statusmessages.interfaces import IStatusMessage


class DefaultPageSelectionView(BrowserView):

    def __call__(self):
        if 'form.button.Save' in self.request.form:
            if not 'objectId' in self.request.form:
                message = _(u'Please select an item to use.')
                msgtype = 'error'
            else:
                objectId = self.request.form['objectId']

                if not objectId in self.context.objectIds():
                    message = _(u'There is no object with short name ${name} '
                                u'in this folder.',
                                mapping={u'name': objectId})
                    msgtype = 'error'
                else:
                    self.context.setDefaultPage(objectId)
                    message = _(u'View changed.')
                    msgtype = 'info'
                    self.request.response.redirect(self.context.absolute_url())
            IStatusMessage(self.request).add(message, msgtype)
        elif 'form.button.Cancel' in self.request.form:
            self.request.response.redirect(self.context.absolute_url())

        return self.index()
