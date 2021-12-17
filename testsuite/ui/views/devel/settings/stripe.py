"""Settings Devel portal View containing credit card details for Stripe payment gateway"""
import logging

from widgetastic.widget import View, TextInput, Select, GenericLocatorWidget, Text

from testsuite.ui.objects import CreditCard, BillingAddress
from testsuite.ui.views.devel import BaseDevelView
from testsuite.ui.views.devel.settings import SettingsTabs

logger = logging.getLogger(__name__)


class BillingAddressForm(View):
    """Billing Address form"""
    ROOT = "//form[@action='/admin/account/payment_details']"
    name = TextInput(id="account_billing_address_name")
    address1 = TextInput(id="account_billing_address_address1")
    address2 = TextInput(id="account_billing_address_address2")
    city = TextInput(id="account_billing_address_city")
    country = Select(id="account_billing_address_country_id")
    state = TextInput(id="account_billing_address_state")
    phone = TextInput(id="account_billing_address_phone")
    postal = TextInput(id="account_billing_address_zip")
    submit = GenericLocatorWidget(".//input[@type='submit']")

    def add(self, address):
        """Adds billing address"""
        self.name.fill(address.name)
        self.address1.fill(address.address)
        self.city.fill(address.city)
        self.country.fill(address.country)
        self.state.fill(address.state)
        self.phone.fill(address.phone)
        self.postal.fill(address.zip)
        self.submit.click()

    @property
    def is_displayed(self):
        return self.name.is_displayed and self.submit.is_displayed


class StripeCCForm(View):
    """Stripe Credit card form"""
    submit_btn = GenericLocatorWidget(".//button[@id='stripe-submit']")

    @View.nested
    class cc_details(View):  # pylint: disable=invalid-name
        """IFrame that contains credit card information"""
        FRAME = ".//form[@id='stripe-form']//iframe"
        cardnumber = TextInput(name="cardnumber")
        expiration = TextInput(name="exp-date")
        cvc = TextInput(name="cvc")
        postal = TextInput(name="postal")

    def add(self, credit_card, postal):
        """Adds a new card to the Stripe form"""
        self.cc_details.cardnumber.fill(credit_card.number)
        self.cc_details.expiration.fill(f"{credit_card.exp_month}{credit_card.exp_year}")
        self.cc_details.cvc.fill(credit_card.cvc)
        self.cc_details.postal.fill(postal)
        self.submit_btn.click()

    @property
    def is_displayed(self):
        return self.submit_btn.is_displayed and self.cc_details.cardnumber.is_displayed


class OTPForm(View):
    """3DS Stripe verification form. OTP test button is hidden in 3 IFrames"""
    FRAME = "html/body/div/iframe[contains(@name, 'StripeFrame')]"

    @View.nested
    class challenge_frame(View):  # pylint: disable=invalid-name
        """Nested IFrame"""
        FRAME = ".//iframe[@id='challengeFrame']"

        @View.nested
        class acs_frame(View):  # pylint: disable=invalid-name
            """Nested IFrame that contains OTP elements"""
            FRAME = ".//iframe[@name='acsFrame']"
            complete_auth = GenericLocatorWidget(".//button[@id='test-source-authorize-3ds']")

    def complete_auth(self):
        """Completes the authentication"""
        self.browser.element(self.challenge_frame.acs_frame.complete_auth).submit()
        self.browser.selenium.switch_to.default_content()


class StripeCCView(BaseDevelView):
    """View for adding credit card to the Stripe payment gateway"""
    path_pattern = '/admin/account/stripe'
    tabs = View.nested(SettingsTabs)
    add_billing_address_btn = Text("//a[@href='/admin/account/stripe/edit']")
    add_cc_details_btn = GenericLocatorWidget("//*[normalize-space(.)='Edit Credit Card Details']")

    address_form = View.nested(BillingAddressForm)
    cc_form = View.nested(StripeCCForm)
    otp_form = View.nested(OTPForm)

    def add_cc_details(self, address: BillingAddress, credit_card: CreditCard):
        """Adds credit card details for the user"""
        self.add_billing_address_btn.wait_displayed()
        self.add_billing_address_btn.click()
        self.address_form.add(address)

        if self.add_cc_details_btn.is_displayed:
            self.add_cc_details_btn.click()
        self.cc_form.wait_displayed()
        self.cc_form.add(credit_card, address.zip)

        if credit_card.sca:
            self.otp_form.complete_auth()
        self.browser.wait_for_element("//*[normalize-space(.)='Credit card number']", timeout=20)

    def prerequisite(self):
        return SettingsTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url
