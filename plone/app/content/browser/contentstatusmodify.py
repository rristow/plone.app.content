from AccessControl import Unauthorized
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import transaction_note
from ZODB.POSException import ConflictError
from zope.publisher.browser import BrowserView


class ContentStatusModifyView(BrowserView):

    def __init__(self, context, request):
        super(ContentStatusModifyView, self).__init__(context, request)

        self.plone_utils = getToolByName(context, 'plone_utils')
        self.contentEditSuccess = 0
        self.plone_log = context.plone_log
        self.new_context = context.portal_factory.doCreate(context)
        self.portal_workflow = self.new_context.portal_workflow
        self.transitions = self.portal_workflow.getTransitionsFor(
            self.new_context)
        self.transition_ids = [t['id'] for t in self.transitions]

    def __call__(self, workflow_action=None, comment='', effective_date=None,
                 expiration_date=None, *args):

        if workflow_action in self.transition_ids \
            and not effective_date \
                and self.context.EffectiveDate() == 'None':
            effective_date = DateTime()

        try:
            self.editContent(self.new_context, effective_date, expiration_date)
            contentEditSuccess = 1
        except Unauthorized:
            pass

        wfcontext = self.context

        # Create the note while we still have access to wfcontext
        note = 'Changed status of %s at %s' % (wfcontext.title_or_id(),
                                               wfcontext.absolute_url())
        if workflow_action in self.transition_ids:
            wfcontext = self.new_context.portal_workflow.doActionFor(
                self.context,
                workflow_action,
                comment=comment)

        if not wfcontext:
            wfcontext = self.new_context

        # The object post-transition could now have ModifyPortalContent
        # permission.
        if not contentEditSuccess:
            try:
                self.editContent(wfcontext, effective_date, expiration_date)
            except Unauthorized:
                pass

        transaction_note(note)

        # If this item is the default page in its parent, attempt to publish
        # that too. It may not be possible, of course
        if self.plone_utils.isDefaultPage(self.new_context):
            parent = self.new_context.aq_inner.aq_parent
            try:
                parent.restrictedTraverse("@@content_status_modify")(
                    workflow_action,
                    comment,
                    effective_date=effective_date,
                    expiration_date=expiration_date)
            except ConflictError:
                raise
            except Exception:
                pass

        self.context.plone_utils.addPortalMessage(_(u'Item state changed.'))
        #return state.set(context=wfcontext)
        return self.request.RESPONSE.redirect(
            wfcontext.absolute_url())

    def editContent(self, obj, effective, expiry):
        kwargs = {}
        # may contain the year
        effective_is_datetime = isinstance(effective, DateTime)
        if effective and (effective_is_datetime or len(effective) > 5):
            kwargs['effective_date'] = effective
        # may contain the year
        if expiry and (isinstance(expiry, DateTime) or len(expiry) > 5):
            kwargs['expiration_date'] = expiry
        self.new_context.plone_utils.contentEdit(obj, **kwargs)
