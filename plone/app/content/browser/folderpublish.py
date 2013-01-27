from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import transaction_note
from zope.publisher.browser import BrowserView


class FolderPublishView(BrowserView):

    def __init__(self, context, request):
        super(FolderPublishView, self).__init__(context, request)
        self.errors = {}

    def __call__(self, workflow_action=None, paths=[],
                 comment='No comment',
                 expiration_date=None, effective_date=None,
                 include_children=False):

        if self.errors:
            return self.template()

        plone_utils = getToolByName(self.context, 'plone_utils')
        failed = plone_utils.transitionObjectsByPaths(
            workflow_action, paths, comment,
            expiration_date, effective_date,
            include_children, REQUEST=self.request,)

        transaction_note(str(paths) + ' transitioned ' + workflow_action)

        # It is necessary to set the context to override context from
        # content_status_modify
        plone_utils.addPortalMessage(_(u'Item state changed.'))
        url = self.request.get('orig_template')
        if url is None:
            url = "%s/view" % self.context.absolute_url()
        return self.request.RESPONSE.redirect(url)
