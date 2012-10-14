from Products.CMFCore.utils import getToolByName
from zope.publisher.browser import BrowserView


class LinkRedirectView(BrowserView):

    def __call__(self):
        context = self.context
        ptool = getToolByName(context, 'portal_properties')
        mtool = getToolByName(context, 'portal_membership')

        redirect_links = getattr(ptool.site_properties, 'redirect_links', False)
        can_edit = mtool.checkPermission('Modify portal content', context)

        if redirect_links and not can_edit:
            if context.getRemoteUrl().startswith('.'):
                # we just need to adapt ../relative/links, /absolute/ones work anyway
                # -> this requires relative links to start with ./ or ../
                context_state = context.restrictedTraverse('@@plone_context_state')
                return context.REQUEST.RESPONSE.redirect(
                            context_state.canonical_object_url()
                            + '/'
                            + context.getRemoteUrl())
            else:
                return context.REQUEST.RESPONSE.redirect(context.getRemoteUrl())
        else:
            # without redirects we get the normal link view at "templates/link_view.pt"
            return self.index()
