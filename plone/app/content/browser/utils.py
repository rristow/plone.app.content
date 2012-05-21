from AccessControl import Unauthorized
from zope.component import getMultiAdapter
from OFS.CopySupport import CopyError
from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.CMFPlone import utils
from Products.CMFPlone import PloneMessageFactory as _
from plone.protect.postonly import check as checkpost
from ZODB.POSException import ConflictError


class ContentUtilViews(BrowserView):

    def objectTitle(self):
        context = aq_inner(self.context)
        title = utils.pretty_title_or_id(context, context)
        return utils.safe_unicode(title)

    def protect(self):
        authenticator = getMultiAdapter((self.context, self.request),
                                        name='authenticator')
        if not authenticator.verify():
            raise Unauthorized
        checkpost(self.request)

    def redirectReferer(self):
        request = self.request
        return request.response.redirect(request.get('HTTP_REFERER'))

    def object_copy(self, ajax=False):
        self.protect()
        context = aq_inner(self.context)
        plone_utils = getToolByName(context, 'plone_utils')
        title = self.objectTitle()
        parent = aq_parent(context)
        try:
            parent.manage_copyObjects(context.getId(), self.request)
            message = _(u'${title} copied.', mapping={u'title': title})
            utils.transaction_note('Copied object %s' % context.absolute_url())
            plone_utils.addPortalMessage(message)
        except CopyError:
            message = _(u'${title} is not copyable.',
                mapping={u'title': title})
            plone_utils.addPortalMessage(message, 'error')

        if ajax:
            pass
        else:
            return self.redirectReferer()

    def object_cut(self, ajax=False):
        self.protect()
        context = aq_inner(self.context)
        title = self.objectTitle()
        plone_utils = getToolByName(context, 'plone_utils')
        lock_info = getMultiAdapter((context, self.request),
                                    name='plone_lock_info')
        if lock_info is not None and lock_info.is_locked():
            message = _(u'${title} is locked and cannot be cut.',
                mapping={u'title': title})
            plone_utils.addPortalMessage(message, 'error')
        else:
            parent = aq_parent(context)
            try:
                parent.manage_cutObjects(context.getId(), self.request)
                message = _(u'${title} cut.', mapping={u'title': title})
                utils.transaction_note('Cut object %s' % (
                    context.absolute_url()))
                plone_utils.addPortalMessage(message)
            except CopyError:
                message = _(u'${title} is not moveable.',
                    mapping={u'title': title})
                plone_utils.addPortalMessage(message, 'error')

        if ajax:
            pass
        else:
            return self.redirectReferer()

    def object_paste(self):
        self.protect()
        context = aq_inner(self.context)
        plone_utils = getToolByName(context, 'plone_utils')

        msg = _(u'Copy or cut one or more items to paste.')
        if context.cb_dataValid():
            try:
                context.manage_pasteObjects(context.REQUEST['__cp'])
                utils.transaction_note('Pasted content to %s' % (
                    context.absolute_url()))
                plone_utils.addPortalMessage(_(u'Item(s) pasted.'))
                return self.redirectReferer()
            except ConflictError:
                raise
            except ValueError:
                msg = _(u'Disallowed to paste item(s).')
            except Unauthorized:
                msg = _(u'Unauthorized to paste item(s).')
            except:  # fallback
                msg = _(u'Paste could not find clipboard content.')

        plone_utils.addPortalMessage(msg, 'error')
        return self.redirectReferer()

    def object_delete(self):
        self.protect()
        context = aq_inner(self.context)
        request = self.request
        parent = aq_parent(context)
        title = self.objectTitle()
        plone_utils = getToolByName(context, 'plone_utils')

        lock_info = getMultiAdapter((context, request),
                                    name='plone_lock_info')

        if lock_info is not None and lock_info.is_locked():
            message = _(u'${title} is locked and cannot be deleted.',
                mapping={u'title': title})
            plone_utils.addPortalMessage(message, type='error')
            return request.response.redirect(context.absolute_url())
        else:
            parent.manage_delObjects(context.getId())
            message = _(u'${title} has been deleted.',
                mapping={u'title': title})
            utils.transaction_note('Deleted %s' % context.absolute_url())
            plone_utils.addPortalMessage(message)
            return request.response.redirect(parent.absolute_url())
