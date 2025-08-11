"""View representations of Product Active docs pages"""

from widgetastic_patternfly4 import PatternflyTable
from widgetastic.widget import View, Text

from testsuite.ui.views.admin.product import BaseProductView
from testsuite.ui.widgets.buttons import ThreescaleDeleteButton, ThreescaleEditButton
from testsuite.ui.widgets import ActiveDocV2Section
from testsuite.ui.navigation import step
from testsuite.ui.widgets.oas3 import Endpoint


class ActiveDocsView(BaseProductView):
    """View representation of Active Docs list page"""

    path_pattern = "/apiconfig/services/{product_id}/api_docs"
    active_docs_table = PatternflyTable(locator=".//table", column_widgets={"Name": Text("./a")})

    @step("ActiveDocsDetailView")
    def detail(self, active_doc):
        """Navigate to active doc detail/preview page"""
        self.active_docs_table.row(name=active_doc["name"]).name.widget.click()

    def prerequisite(self):
        return BaseProductView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.active_docs_table.is_displayed
            and self.path in self.browser.url
        )


class ActiveDocsDetailView(BaseProductView):
    """View representation of Active Docs Detail page"""

    path_pattern = "/apiconfig/services/{product_id}/api_docs/{active_doc_id}/preview"
    delete_btn = ThreescaleDeleteButton()
    edit_btn = ThreescaleEditButton()

    def __init__(self, parent, product, active_doc):
        super().__init__(parent, product, active_doc_id=active_doc.entity_id)

    @View.nested
    # pylint: disable=invalid-name
    class oas2(View):
        """OAS version 2 section"""

        expand_operations_link = Text(locator="//*[contains(@class, 'expandResource')]")
        collapse_operations_link = Text(locator="//*[contains(@class, 'collapseResource')]")
        active_docs_section = ActiveDocV2Section()

        def make_request(self, endpoint):
            """
            Make request on preview page
            :param endpoint: string of endpoint which should be tried
            :return:
            """
            self.expand_operations_link.click()
            self.active_docs_section.try_it_out(endpoint)

    @View.nested
    # pylint: disable=invalid-name
    class oas3(View):
        """OAS version 3 section"""

        server = Text("//label[@for='servers']/select/option")
        endpoint = View.nested(Endpoint)

    def prerequisite(self):
        return ActiveDocsView

    @property
    def is_displayed(self):
        return (
            BaseProductView.is_displayed.fget(self)
            and self.edit_btn.is_displayed
            and self.delete_btn.is_displayed
            and self.path in self.browser.url
        )
