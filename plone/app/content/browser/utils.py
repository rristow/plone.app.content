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
from Products.CMFCore.exceptions import ResourceLockedError
from Products.PythonScripts.standard import url_unquote


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

    def redirectFolderContents(self):
        contents_url = self.context.absolute_url() + '/@@folder_contents'
        return self.request.response.redirect(contents_url)

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
                import traceback
                print traceback.format_exc()
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

    def folder_delete(self):
        self.protect()
        context = aq_inner(self.context)
        req = self.request
        paths = req.get('paths', [])

        putils = getToolByName(context, 'plone_utils')
        message = _(u'Please select one or more items to delete.')

        # a hint to the link integrity code to indicate the number of events to
        # expect, so that all integrity breaches can be handled in a single
        # form only;  normally the adapter (LinkIntegrityInfo) should be used
        # here, but this would make CMFPlone depend on an import from
        # LinkIntegrity, which it shouldn't...
        req.set('link_integrity_events_to_expect', len(paths))
        success, failure = putils.deleteObjectsByPaths(paths, REQUEST=req)

        if success:
            message = _(u'Item(s) deleted.')

        if failure:
            # we want a more descriptive message when trying
            # to delete locked item
            other = []
            locked = []
            message = str(failure)
            for key, value in failure.items():
                # below is a clever way to check exception type
                try:
                    raise value
                except ResourceLockedError:
                    locked.append(key)
                except:
                    other.append(key)
                else:
                    other.append(key)
            # locked contains ids of items that cannot be deleted,
            # because they are locked; other contains ids of items
            # that cannot be deleted for other reasons;
            # now we need to construct smarter error message
            mapping = {}

            if locked:
                mapping[u'lockeditems'] = ', '.join(locked)
                message = _(
                    u'These items are locked for editing: ${lockeditems}.',
                    mapping=mapping)
            else:
                mapping[u'items'] = ', '.join(other)
                message = _(u'${items} could not be deleted.', mapping=mapping)

        putils.addPortalMessage(message)
        return req.response.redirect('%s/@@folder_contents' % (
            context.absolute_url()))

    def folder_cut(self):
        context = aq_inner(self.context)
        self.protect()
        plone_utils = getToolByName(context, 'plone_utils')
        req = self.request
        if 'paths' in req:
            ids = [p.split('/')[-1] or p.split('/')[-2] for p in req['paths']]

            try:
                context.manage_cutObjects(ids, req)
            except CopyError:
                message = _(u'One or more items not moveable.')
                plone_utils.addPortalMessage(message, 'error')
            except AttributeError:
                message = _(u'One or more selected items '
                            u'is no longer available.')
                plone_utils.addPortalMessage(message, 'error')
            except ResourceLockedError:
                message = _(u'One or more selected items is locked.')
                plone_utils.addPortalMessage(message, 'error')
            else:
                utils.transaction_note('Cut %s from %s' % (
                    (str(ids)), context.absolute_url()))
                message = _(u'${count} item(s) cut.',
                            mapping={u'count': len(ids)})

                context.plone_utils.addPortalMessage(message)
            return self.redirectFolderContents()
        else:
            plone_utils.addPortalMessage(
                _(u'Please select one or more items to cut.'), 'error')
            return self.redirectFolderContents()

    def folder_paste(self):
        self.protect()
        context = aq_inner(self.context)
        req = self.request
        msg = _(u'Copy or cut one or more items to paste.')
        plone_utils = getToolByName(context, 'plone_utils')

        if context.cb_dataValid:
            try:
                context.manage_pasteObjects(req['__cp'])
                utils.transaction_note('Pasted content to %s' % (
                    context.absolute_url()))
                plone_utils.addPortalMessage(_(u'Item(s) pasted.'))
                return self.redirectFolderContents()
            except ConflictError:
                raise
            except ValueError:
                msg = _(u'Disallowed to paste item(s).')
            except Unauthorized:
                msg = _(u'Unauthorized to paste item(s).')
            except:  # fallback
                msg = _(u'Paste could not find clipboard content.')

        plone_utils.addPortalMessage(msg, 'error')
        return self.redirectFolderContents()

    def folder_copy(self):
        self.protect()
        req = self.request
        context = aq_inner(self.context)
        plone_utils = getToolByName(context, 'plone_utils')
        if 'paths' in req:
            ids = [p.split('/')[-1] or p.split('/')[-2] for p in req['paths']]

            try:
                context.manage_copyObjects(ids, req, req.response)
            except CopyError:
                message = _(u'One or more items not copyable.')
                plone_utils.addPortalMessage(message, 'error')
                return self.redirectFolderContents()
            except AttributeError:
                message = _(u'One or more selected items '
                            u'is no longer available.')
                plone_utils.addPortalMessage(message, 'error')
                return self.redirectFolderContents()
            utils.transaction_note('Copied %s from %s' % (
                str(ids), context.absolute_url()))

            message = _(u'${count} item(s) copied.',
                mapping={u'count': len(ids)})

            plone_utils.addPortalMessage(message)
            return self.redirectFolderContents()

        plone_utils.addPortalMessage(
            _(u'Please select one or more items to copy.'), 'error')
        return self.redirectFolderContents()

    def folder_rename(self, paths=[], new_ids=[], new_titles=[]):
        self.protect()
        context = aq_inner(self.context)
        req = self.request
        plone_utils = getToolByName(context, 'plone_utils')
        orig_template = req.get('orig_template', None)
        change_template = paths and orig_template is not None
        message = None
        if change_template:
            # We were called by 'object_rename'.  So now we take care that the
            # user is redirected to the object with the new id.
            portal_url = getToolByName(context, 'portal_url')
            portal = portal_url.getPortalObject()
            obj = portal.restrictedTraverse(paths[0])
            new_id = new_ids[0]
            obid = obj.getId()
            if new_id and new_id != obid:
                orig_path = obj.absolute_url_path()
                # replace the id in the object path with the new id
                base_path = orig_path.split('/')[:-1]
                base_path.append(new_id)
                new_path = '/'.join(base_path)
                orig_template = orig_template.replace(url_unquote(orig_path),
                                                      new_path)
                req.set('orig_template', orig_template)
                message = _(u"Renamed '${oldid}' to '${newid}'.",
                            mapping={u'oldid': obid, u'newid': new_id})

        success, failure = plone_utils.renameObjectsByPaths(
            paths, new_ids, new_titles, REQUEST=req)

        if message is None:
            message = _(u'${count} item(s) renamed.',
                        mapping={u'count': str(len(success))})

        if failure:
            message = _(u'The following item(s) could not be '
                        u'renamed: ${items}.',
                        mapping={u'items': ', '.join(failure.keys())})

        context.plone_utils.addPortalMessage(message)
        return self.redirectFolderContents()
