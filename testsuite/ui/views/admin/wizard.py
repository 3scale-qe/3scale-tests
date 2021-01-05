""" Introduction wizard pages module"""
from widgetastic.widget import (
    View
)
from testsuite.ui.widgets import Link


class WizardCommonView(View):
    """
    All wizard pages common objects
    """
    close_wizard_link = Link("//a[@href='/p/admin/dashboard']")


class WizardIntroView(WizardCommonView):
    """
    Representation of Wizard introduction view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/intro'

    # pylint: disable=pointless-statement
    def close_wizard(self):
        """
        Method which close wizard
        """
        self.close_wizard_link.click()

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url


class WizardExplainView(WizardCommonView):
    """
    Representation of Wizard explain view page object.
    """
    endpoint_path = '/p/admin/onboarding/wizard/explain'

    @property
    def is_displayed(self):
        return self.endpoint_path in self.browser.url
