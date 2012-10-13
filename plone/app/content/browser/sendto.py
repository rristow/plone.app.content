from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import transaction_note
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from zope.component import getMultiAdapter


class SendToView(BrowserView):
    """Send a URL to a friend
    """

    def __call__(self):
        request = self.request
        context = self.context
        status = IStatusMessage(request)
        plone_utils = getToolByName(context, 'plone_utils')
        site = getToolByName(context, 'portal_url').getPortalObject()
        pretty_title_or_id = plone_utils.pretty_title_or_id

        # Find the view action.
        context_state = context.restrictedTraverse("@@plone_context_state")
        url = context_state.view_url()

        variables = {
            'send_from_address': request.send_from_address,
            'send_to_address': request.send_to_address,
            'subject': pretty_title_or_id(context),
            'url': url,
            'title': pretty_title_or_id(context),
            'description': context.Description(),
            'comment': request.get('comment', None),
            'envelope_from': site.getProperty('email_from_address'),
            }

        try:
            plone_utils.sendto(**variables)
        except ConflictError:
            raise
        except:  # TODO Too many things could possibly go wrong. So we catch all.
            exception = plone_utils.exceptionString()
            message = _(u'Unable to send mail: ${exception}',
                        mapping={u'exception': exception})
            status.addStatusMessage(message, type='error')
            self.redirect()
            return

        # TODO We are not committing anything, right?
        tmsg = 'Sent page %s to %s' % (url, request.send_to_address)
        transaction_note(tmsg)

        status.addStatusMessage(_(u'Mail sent.'))
        self.redirect()
        return

    def redirect(self):
        pcs = getMultiAdapter((self.context, self.request),
                              name='plone_context_state')
        self.request.RESPONSE.redirect(pcs.canonical_object_url())
