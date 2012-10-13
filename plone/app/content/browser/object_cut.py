from zope.publisher.browser import BrowserView
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone import PloneMessageFactory as _
from OFS.CopySupport import CopyError
from zope.component import queryMultiAdapter


class ObjectCut(BrowserView):
    
    def __call__(self):
        context = self.context
        context_state = context.restrictedTraverse('@@plone_context_state')
        self.canonical_object_url = context_state.canonical_object_url()
        self.obj_title = safe_unicode(context.title_or_id())
        if self.check_locks():
            return self.request.RESPONSE.redirect(self.canonical_object_url)

        parent = context.aq_inner.aq_parent
        try:
            parent.manage_cutObjects(self.context.getId(), self.request)
        except CopyError:
            message = _(u'${title} is not moveable.',
                        mapping={u'title': self.obj_title})
            context.plone_utils.addPortalMessage(message, 'error')
            return self.request.RESPONSE.redirect(self.canonical_object_url)

        message = _(u'${title} cut.', mapping={u'title': self.obj_title})
        transaction_note('Cut object %s' % self.canonical_object_url)

        self.context.plone_utils.addPortalMessage(message)
        return self.request.RESPONSE.redirect(self.canonical_object_url)

    def check_locks(self):
        lock_info = queryMultiAdapter((self.context, self.request),
                                        name='plone_lock_info')
        if lock_info is not None and lock_info.is_locked():
            message = _(u'${title} is locked and cannot be cut.',
                        mapping={u'title': self.obj_title})
            self.context.plone_utils.addPortalMessage(message, 'error')
            return 1

