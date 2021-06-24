"""View for Stripe manipulation"""
import backoff
from widgetastic.widget import View, TextInput, Select, GenericLocatorWidget

from testsuite.ui.views.devel import BaseDevelView
from testsuite.ui.views.devel.settings import SettingsTabs
from testsuite.ui.widgets import Link


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


class StripeCCForm(View):
    """Stripe Credit card form"""
    submit_btn = GenericLocatorWidget("//button[@id='stripe-submit']")

    def add(self, credit_card, postal):
        """Adds a new card to the Stripe form"""
        stripe_frame = self.browser.selenium.find_elements_by_tag_name("iframe")[0]
        self.browser.selenium.switch_to.frame(stripe_frame)
        self._element('cardnumber').send_keys(credit_card.number)
        self._element('exp-date').send_keys(f"{credit_card.exp_month}{credit_card.exp_year}")
        self._element('cvc').send_keys(credit_card.cvc)
        self._element('postal').send_keys(postal)
        self.browser.selenium.switch_to.default_content()
        self.submit_btn.click()

    def _element(self, name):
        return self.browser.selenium.find_element_by_name(name)


class OTPForm(View):
    """3DS verification form"""
    def complete_auth(self):
        """Completes the authentication"""
        self._switch()
        self.browser.selenium.find_element_by_id('test-source-authorize-3ds').click()
        self.browser.selenium.switch_to.default_content()

    def _switch_frame(self, name):
        self.browser.selenium.switch_to.frame(self.browser.selenium.find_element_by_xpath(name))

    def _switch(self):
        # pylint: disable=unused-argument
        def _switch_default(detail):
            self.browser.selenium.switch_to.default_content()

        @backoff.on_exception(backoff.fibo, Exception, max_tries=8, jitter=None, on_backoff=_switch_default)
        def _otp_frame_switch():
            self._switch_frame("/html/body/div[1]/iframe")
            self._switch_frame("//iframe[@id='challengeFrame']")
            self._switch_frame("//iframe[@name='acsFrame']")

        return _otp_frame_switch()


class StripeCCView(BaseDevelView):
    """View for adding credit card to the stripe"""
    path_pattern = '/admin/account/stripe'
    tabs = View.nested(SettingsTabs)
    add_billing_address_btn = Link("//a[@href='/admin/account/stripe/edit']")
    address_form = View.nested(BillingAddressForm)
    cc_form = View.nested(StripeCCForm)
    otp_form = View.nested(OTPForm)

    def add_cc_details(self, address, credit_card, otp=False):
        """Adds credit card details"""
        if self.add_billing_address_btn.is_displayed:
            self.add_billing_address_btn.click()
        self.address_form.add(address)
        self.cc_form.add(credit_card, address.zip_code)
        if otp:
            self.otp_form.complete_auth()
        self.browser.wait_for_element("//*[normalize-space(.)='Credit card number']", timeout=20)

    def prerequisite(self):
        return SettingsTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url
