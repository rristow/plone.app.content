from AccessControl import Unauthorized
from Acquisition import aq_inner
from zope.publisher.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from zope.component import getMultiAdapter


class ConstrainTypesView(BrowserView):

    def __init__(self, context, request):
        super(ConstrainTypesView, self).__init__(context, request)
        self.errors = {}

    def __call__(self):
        if 'form.button.Save' in self.request.form:
            authenticator = getMultiAdapter((self.context, self.request),
                                            name=u"authenticator")
            if not authenticator.verify():
                raise Unauthorized

            self.set_constrain_types()
            plone_utils = getToolByName(self.context, 'plone_utils')
            if self.errors:
                plone_utils.addPortalMessage(
                    _(u'Please correct the indicated errors.'), 'error')
                return self.index()

            plone_utils.addPortalMessage(_(u'Changes made.'))
            context_state = getMultiAdapter((self.context, self.request),
                                            name=u'plone_context_state')
            url = context_state.view_url()
            self.request.response.redirect(url)
            return ''
        elif 'form.button.Cancel' in self.request.form:
            self.request.response.redirect(self.context.absolute_url())
            return ''
        else:
            return self.index()

    def set_constrain_types(self):
        context = aq_inner(self.context)
        constrain_types_mode = self.request.form.get('constrainTypesMode', [])
        current_prefer = self.request.form.get('currentPrefer', [])
        current_allow = self.request.form.get('currentAllow', [])

        not_found = [t for t in current_allow if t not in current_prefer]
        if not_found:
            msg = _(u'You cannot have a type as secondary type without having '
                    u'it allowed. You have selected ${types}.',
                    mapping={u'types': ', '.join(not_found)})
            self.errors['currentPrefer'] = msg

        # due to the logic in #6151 we actually need to do the following:
        # - if a type is in "currentPrefer", then it's automatically
        #   also an "locallyAllowedTypes" type.
        # - types which are in "currentAllow" are to be removed from the
        #   "immediatelyAddableTypes" list.
        #
        # That means:
        # - users select types which they want to see in the menu using the
        #   "immediatelyAddableTypes" list
        # - if the user wants to see a certain type _only_ in the "more ..."
        #   form, then they select it inside the "locallyAllowedTypes" list.

        immediately_addable_types = [t for t in current_prefer
                                     if not t in current_allow]
        locally_allowed_types = [t for t in current_prefer]

        context.setConstrainTypesMode(constrain_types_mode)
        context.setLocallyAllowedTypes(locally_allowed_types)
        context.setImmediatelyAddableTypes(immediately_addable_types)
