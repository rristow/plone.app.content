from AccessControl import Unauthorized
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
        if self.request.get('REQUEST_METHOD') != 'POST':
            # Simply display the form.
            return self.index()
        authenticator = getMultiAdapter(
            (self.context, self.request), name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
        # Validate the form
        self.errors = self.validate()
        if self.errors:
            return self.index()

        # Send the email and redirect to the object.
        self.send()
        self.redirect()

    def send(self):
        request = self.request
        status = IStatusMessage(request)
        plone_utils = getToolByName(self.context, 'plone_utils')
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        pretty_title_or_id = plone_utils.pretty_title_or_id

        pcs = getMultiAdapter((self.context, self.request),
                              name='plone_context_state')
        url = pcs.canonical_object_url()

        variables = {
            'send_from_address': request.send_from_address,
            'send_to_address': request.send_to_address,
            'subject': pretty_title_or_id(self.context),
            'url': url,
            'title': pretty_title_or_id(self.context),
            'description': self.context.Description(),
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
            return

        # TODO We are not committing anything, right?
        tmsg = 'Sent page %s to %s' % (url, request.send_to_address)
        transaction_note(tmsg)

        status.addStatusMessage(_(u'Mail sent.'))

    def redirect(self):
        pcs = getMultiAdapter((self.context, self.request),
                              name='plone_context_state')
        self.request.RESPONSE.redirect(pcs.canonical_object_url())

    def validate(self):
        send_to_address = self.request.get('send_to_address')
        send_from_address = self.request.get('send_from_address')
        plone_utils = getToolByName(self.context, 'plone_utils')
        errors = {}
        if not send_to_address:
            errors['send_to_address'] = _(u'Please submit an email address.')
        elif not plone_utils.validateEmailAddresses(send_to_address):
            errors['send_to_address'] = _(
                u'Please submit a valid email address.')

        if not send_from_address:
            errors['send_from_address'] = _(u'Please submit an email address.')
        elif not plone_utils.validateSingleEmailAddress(send_from_address):
            errors['send_from_address'] = _(
                u'Please submit a valid email address.')

        if errors:
            status = IStatusMessage(self.request)
            status.addStatusMessage(u'Please correct the indicated errors.',
                                    type='error')
        return errors
