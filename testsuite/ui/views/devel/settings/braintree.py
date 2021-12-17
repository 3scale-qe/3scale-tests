"""Settings Devel portal View containing credit card details for Braintree payment gateway"""
from widgetastic.widget import View, TextInput, Select, GenericLocatorWidget, Text
from widgetastic_patternfly import Button

from testsuite.ui.objects import BillingAddress, CreditCard
from testsuite.ui.views.devel import BaseDevelView
from testsuite.ui.views.devel.settings import SettingsTabs
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class CustomerForm(View):
    """Billing Address form"""
    ROOT = "//form[@id='customer_form']"
    first_name = TextInput(id="customer_first_name")
    last_name = TextInput(id="customer_last_name")
    phone = TextInput(id="customer_phone")
    company = TextInput(id="customer_credit_card_billing_address_company")
    address = TextInput(id="customer_credit_card_billing_address_street_address")
    postal = TextInput(id="customer_credit_card_billing_address_postal_code")
    city = TextInput(id="customer_credit_card_billing_address_locality")
    state = TextInput(id="customer_credit_card_billing_address_region")
    country = Select(id="customer_credit_card_billing_address_country_name")
    save = Button("Save details")

    def add(self, address: BillingAddress):
        """Add Billing information"""
        self.first_name.fill("test")
        self.last_name.fill("test")
        self.phone.fill(address.phone)
        self.company.fill(address.name)
        self.address.fill(address.address)
        self.postal.fill(address.zip)
        self.city.fill(address.city)
        self.state.fill(address.state)
        self.country.fill(address.country)


class BraintreeCCForm(View):
    """Braintree Credit card form"""
    cc_number = TextInput(id="credit-card-number")
    cvv = TextInput(id="cvv")
    expiration = TextInput(id="expiration")

    def add(self, credit_card: CreditCard):
        """Adds a new card for Braintree"""
        self._iframe_fill(
            "braintree-hosted-field-number", self.cc_number, credit_card.number)
        self._iframe_fill(
            "braintree-hosted-field-cvv", self.cvv, credit_card.cvc)
        self._iframe_fill(
            "braintree-hosted-field-expirationDate", self.expiration,
            f"{credit_card.exp_month:02d}{credit_card.exp_year}")

    def _iframe_fill(self, frame_id, widget, value):
        frame = self.browser.selenium.find_element_by_xpath(f"//iframe[@name='{frame_id}']")
        self.browser.selenium.switch_to.frame(frame)
        widget.fill(value)
        self.browser.selenium.switch_to.default_content()


class OTPForm(View):
    """3DS Braintree verification form"""
    FRAME = '//iframe[@id="Cardinal-CCA-IFrame"]'
    otp_input = TextInput(name="challengeDataEntry")
    submit = ThreescaleSubmitButton()

    def complete_auth(self):
        """Complete authentication"""
        self.otp_input.wait_displayed()
        self.otp_input.fill("1234")
        self.browser.element(self.submit).submit()
        self.browser.selenium.switch_to.default_content()


class BraintreeCCView(BaseDevelView):
    """View for adding credit card to the Braintree payment gateway"""
    path_pattern = '/admin/account/braintree_blue'
    tabs = View.nested(SettingsTabs)
    add_billing_address = Text(
        "//*[normalize-space(.)='Add Credit Card Details and Billing Address']/a")
    edit_billing_address = Text(
        "//*[normalize-space(.)='Edit Credit Card Details and Billing Address']/a")
    otp_tmp = GenericLocatorWidget("//div[@id='Cardinal-Modal']")

    customer_form = View.nested(CustomerForm)
    cc_form = View.nested(BraintreeCCForm)
    otp_form = View.nested(OTPForm)

    def add_cc_details(self, address: BillingAddress, credit_card: CreditCard):
        """Adds credit card details for the user"""
        if self.add_billing_address.is_displayed:
            self.add_billing_address.click()
        if self.edit_billing_address.is_displayed:
            self.edit_billing_address.click()
        self.customer_form.wait_displayed(timeout="20s")
        self.customer_form.add(address)

        self.cc_form.add(credit_card)
        self.customer_form.save.click()

        if credit_card.sca:
            self.otp_form.complete_auth()
        self.browser.wait_for_element("//*[normalize-space(.)='Credit card number']", timeout=20)

    def prerequisite(self):
        return SettingsTabs

    @property
    def is_displayed(self):
        return self.path in self.browser.url
