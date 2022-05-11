"""View representations of Billing pages"""

from widgetastic.widget import Select, ConditionalSwitchableView, View, TextInput

from testsuite.ui.views.admin.audience import BaseAudienceView
from testsuite.ui.widgets import AudienceTable, ThreescaleCheckBox, ThreescaleDropdown
from testsuite.ui.widgets.buttons import ThreescaleSubmitButton


class BillingView(BaseAudienceView):
    """View representation of Earnings by Month page"""
    path_pattern = '/finance'
    table = AudienceTable("//*[@class='data']")

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.table.is_displayed and self.path in self.browser.url


class ChargingForm(View):
    """Charging form for 3scale billing"""
    ROOT = '//form[contains(@id, "edit_finance_billing_strategy")]'
    charging = ThreescaleCheckBox('//input[@id="finance_billing_strategy_charging_enabled"]')
    currency = ThreescaleDropdown("//*[@id='finance_billing_strategy_currency']")
    save_btn = ThreescaleSubmitButton()

    def change_currency(self, value):
        """Change 3scale billing currency"""
        if self.currency.selected_value() != value:
            self.currency.select_by_value(value)
            self.save_btn.click()

    @property
    def is_displayed(self):
        return self.charging.is_displayed and self.save_btn.is_displayed


class GatewayForm(View):
    """Form where payment gateway options are located"""
    ROOT = '//form[@id="payment-gateway-form"]'
    gateway = Select(id='account_payment_gateway_type')
    options = ConditionalSwitchableView(reference='gateway')
    save_btn = ThreescaleSubmitButton()

    # pylint: disable=undefined-variable
    @options.register('Stripe')
    class StripeForm(View):
        """Form for Stripe gateway integration"""
        ROOT = '//*[@id="payment_gateway_stripe"]'
        secret_key = TextInput(id='account_payment_gateway_options_login')
        publishable_key = TextInput(id='account_payment_gateway_options_publishable_key')
        webhook = TextInput(id='account_payment_gateway_options_endpoint_secret')

    # pylint: disable=undefined-variable
    @options.register('Braintree (Blue Platform)')
    class BraintreeForm(View):
        """Form for Braintree gateway integration"""
        ROOT = '//*[@id="payment_gateway_braintree_blue"]'
        public_key = TextInput(id='account_payment_gateway_options_public_key')
        merchant_id = TextInput(id='account_payment_gateway_options_merchant_id')
        private_key = TextInput(id='account_payment_gateway_options_private_key')
        three_ds = ThreescaleCheckBox('//input[@id="account_payment_braintree_blue_three_ds_enabled"]')

    @property
    def is_displayed(self):
        return self.gateway.is_displayed and self.save_btn.is_displayed


class BillingSettingsView(BaseAudienceView):
    """View representation of Charging & Gateway page"""
    path_pattern = '/finance/settings'
    charging_form = View.nested(ChargingForm)
    gateway_form = View.nested(GatewayForm)

    def charging(self, enable: bool):
        """Enable/disable charging"""
        if enable != self.charging_form.charging.is_checked():
            self.charging_form.charging.check(enable)
            self.charging_form.save_btn.click()

    def stripe(self, secret_key: str, pub_key: str, webhook: str):
        """Set up Stripe as billing gateway if not already enabled"""
        if self.gateway_form.gateway.all_selected_values[0] == 'stripe':
            return
        self.gateway_form.gateway.select_by_value('stripe')
        self.gateway_form.options.fill({
            'secret_key': secret_key,
            'publishable_key': pub_key,
            'webhook': webhook,
        })
        self.save_changes()

    def braintree(self, pub_key: str, merch_id: str, private_key: str, three_ds: bool):
        """
        Set up Braintree as billing gateway if not already enabled.
        Method also ensures if 3D Secure is correctly selected.
        """
        self.gateway_form.gateway.select_by_value('braintree_blue')
        self.gateway_form.options.fill({
            'public_key': pub_key,
            'merchant_id': merch_id,
            'private_key': private_key,
        })
        self.gateway_form.options.three_ds.check(three_ds)
        self.save_changes()

    def save_changes(self):
        """Save changes for billing settings View"""
        self.browser.click(self.gateway_form.save_btn, ignore_ajax=True)
        if self.browser.alert_present:
            self.browser.handle_double_alert()

    def prerequisite(self):
        return BaseAudienceView

    @property
    def is_displayed(self):
        return BaseAudienceView.is_displayed.fget(self) and self.browser.title.text == 'Charging & Gateway' and \
            self.charging_form.is_displayed and self.gateway_form.is_displayed
