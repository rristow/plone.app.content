from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.publisher.browser import BrowserView


class ContentStatusHistoryView(BrowserView):

    template = ViewPageTemplateFile('content_status_history.pt')

    def __init__(self, context, request):
        super(ContentStatusHistoryView, self).__init__(context, request)

        self.plone_utils = getToolByName(context, 'plone_utils')
        self.errors = {}

    def __call__(self, workflow_action=None, paths=[], comment="",
                 effective_date=None, expiration_date=None,
                 include_children=False, *args):

        if self.request.get('form.button.Cancel', None):
            return self.request.RESPONSE.redirect(
                "%s/view" % self.context.absolute_url())

        if self.request.get('form.submitted', None):
            self.validate(workflow_action=workflow_action, paths=paths)
            if self.errors:
                self.plone_utils.addPortalMessage(
                    _(u'Please correct the indicated errors.'), 'error')
                return self.template()

        if self.request.get('form.button.Publish', None):
            return self.context.restrictedTraverse('content_status_modify')(
                workflow_action=workflow_action,
                comment=comment,
                effective_date=effective_date,
                expiration_date=expiration_date)

        if self.request.get('form.button.FolderPublish', None):
            self.restricedTraverse('folder_publish')(
                workflow_action=workflow_action,
                paths=paths,
                comment=comment,
                expiration_date=expiration_date,
                effective_date=effective_date,
                include_children=include_children)

        return self.template()

    def validate(self, workflow_action=None, paths=[]):
        if workflow_action is None:
            self.errors['workflow_action'] = _(
                u'You must select a publishing action.')

        if not paths:
            self.errors['paths'] = _(
                u'You must select content to change.')
            # If there are no paths, it's mostly a mistake
            # Set paths using orgi_paths, otherwise users are getting confused
            orig_paths = self.request.get('orig_paths')
            self.request.set('paths', orig_paths)
