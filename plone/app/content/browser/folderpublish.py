from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import transaction_note
from zope.publisher.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class FolderPublish(BrowserView):

    template = ViewPageTemplateFile('content_status_modify.pt')

    def __class__(self, workflow_action=None, paths=[], comment='No comment',
                  expiration_date=None, effective_date=None,
                  include_children=False):
        plone_utils = self.context.plone_utils

        if workflow_action is None:
            self.context.plone_utils.addPortalMessage(
                _(u'You must select a publishing action.'), 'error')
            return state.set(status='failure')
        if not paths:
            self.context.plone_utils.addPortalMessage(
                _(u'You must select content to change.'), 'error')
            return state.set(status='failure')

        failed = plone_utils.transitionObjectsByPaths(
            workflow_action, paths, comment,
            expiration_date, effective_date,
            include_children, REQUEST=self.request)

        transaction_note(str(paths) + ' transitioned ' + workflow_action)

        # It is necessary to set the context to override context from
        # content_status_modify
        self.context.plone_utils.addPortalMessage(_(u'Item state changed.'))
        return state.set(context=context)
