from plone.autoform.form import AutoExtensibleForm
from Products.CMFPlone import PloneMessageFactory as PC_
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.interface import implements
from zope.interface import Interface
from zope.interface import invariant
from zope.interface.exceptions import Invalid
from zope.schema import List, Choice
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

#XXX These constants should eventually be imported from the interfaces
# but they will only be available there in 4.3b3
ACQUIRE = -1  # acquire locallyAllowedTypes from parent (default)
DISABLED = 0  # use default behavior of PortalFolder which uses the
              # FTI information
ENABLED = 1   # allow types from locallyAllowedTypes only

ST = lambda key, txt, default: SimpleTerm(value=key,
                                          title=PC_(txt, default=default))
possible_constrain_types = SimpleVocabulary(
    [ST(ACQUIRE, u'constraintypes_acquire_label',
                 u'Use parent folder settings'),
     ST(DISABLED, 'constraintypes_disable_label', u'Use portal default'),
     ST(ENABLED, u'constraintypes_enable_label', u'Select manually')
     ])


class ValidTypes(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        constrain_aspect = ISelectableConstrainTypes(context)
        items = []
        for type_ in constrain_aspect.getDefaultAddableTypes():
            items.append(SimpleTerm(value=type_.getId(), title=type_.Title()))
        return SimpleVocabulary(items)

ValidTypesFactory = ValidTypes()


class IConstrainForm(Interface):

    constrain_types_mode = Choice(
        title=PC_("label_type_restrictions", default="Type restrictions"),
        description=PC_("help_add_restriction_mode",
                        default="Select the restriction policy "
                        "in this location"),
        vocabulary=possible_constrain_types
    )

    allow = List(
        title=PC_("label_immediately_addable_types", default="Allowed types"),
        description=PC_("help_immediately_addable_types",
                        default="Controls what types are addable "
                        "in this location"),
        value_type=Choice(
            source="plone.app.content.browser.constraintypes.validtypes"),
    )

    allow_2nd_step = List(
        title=PC_("label_locally_allowed_types", default="Secondary types"),
        description=PC_("help_locally_allowed_types", default=""
                        "Select which types should be available in the "
                        "'More&hellip;' submenu <em>instead</em> of in the "
                        "main pulldown. "
                        "This is useful to indicate that these are not the "
                        "preferred types "
                        "in this location, but are allowed if your really "
                        "need them."
                        ),
        value_type=Choice(
            source="plone.app.content.browser.constraintypes.validtypes"),
    )

    @invariant
    def legal_not_immediately_addable(data):
        missing = []
        for one_allowed_2nd_step in data.allow_2nd_step:
            if one_allowed_2nd_step not in data.allow:
                missing.append(one_allowed_2nd_step)
        if missing:
            raise Invalid(
                PC_("You cannot have a type as secondary type without "
                    "having it allowed. You have selected ${types}s.",
                    mapping=dict(types=", ".join(missing))))
        return True


class FormContentAdapter(object):
    """
    Adapter to allow z3c.form to store the right values on the content.
    WARNING! This Adapter cannot change invariants.
    It is up to YOU to do this in your safe handler!
    """
    def __init__(self, context):
        self.context = ISelectableConstrainTypes(context)

    @property
    def constrain_types_mode(self):
        return self.context.getConstrainTypesMode()

    @constrain_types_mode.setter
    def constrain_types_mode(self, value):
        self.context.setConstrainTypesMode(value)

    @property
    def allow(self):
        return self.context.getLocallyAllowedTypes()

    @allow.setter
    def allow(self, value):
        self.context.setLocallyAllowedTypes(value)

    @property
    def allow_2nd_step(self):
        immediately_allowed = self.context.getImmediatelyAddableTypes()
        return [t for t in self.context.getLocallyAllowedTypes()
                if t not in immediately_allowed]

    @allow_2nd_step.setter
    def allow_2nd_step(self, value):
        locally_allowed = self.context.getLocallyAllowedTypes()
        self.context.setImmediatelyAddableTypes([t for t in locally_allowed
                                                 if t not in value])


class ValidTypes(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        constrain_aspect = ISelectableConstrainTypes(context)
        items = []
        for type_ in constrain_aspect.getDefaultAddableTypes():
            items.append(SimpleTerm(value=type_.getId(), title=type_.Title()))
        return SimpleVocabulary(items)

ValidTypesFactory = ValidTypes()


class ConstrainTypesView(AutoExtensibleForm, form.EditForm):

    schema = IConstrainForm
    ignoreContext = False
    label = PC_("heading_set_content_type_restrictions",
                default="Restrict what types of content can be added")
    template = ViewPageTemplateFile("templates/constraintypes.pt")

    def getContent(self):
        return ISelectableConstrainTypes(self.context)

    def updateFields(self):
        super(ConstrainTypesView, self).updateFields()
        self.fields['allow'].widgetFactory = CheckBoxFieldWidget
        self.fields['allow_2nd_step'].widgetFactory = CheckBoxFieldWidget

    def updateWidgets(self):
        super(ConstrainTypesView, self).updateWidgets()
        self.widgets['allow'].addClass('allow_form')
        self.widgets['allow_2nd_step'].addClass('allow_2nd_step_form')
        self.widgets['constrain_types_mode'].addClass(
            'constrain_types_mode_form')

    @button.buttonAndHandler(u'Cancel')
    def handleCancel(self, action):
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)

    @button.buttonAndHandler(u'Save')
    def handleSave(self, action):
        data, errors = self.extractData()

        if errors:
            return

        immediately_addable_types = [t for t in data['allow']
                                     if t not in data['allow_2nd_step']]
        locally_allowed_types = data['allow']
        aspect = ISelectableConstrainTypes(self.context)
        aspect.setConstrainTypesMode(data['constrain_types_mode'])
        aspect.setLocallyAllowedTypes(locally_allowed_types)
        aspect.setImmediatelyAddableTypes(immediately_addable_types)
        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)
