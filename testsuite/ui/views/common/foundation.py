"""
Module contains Base View used for all Views that are the same in Admin and Master.
"""
from widgetastic.widget import GenericLocatorWidget, View, Text


class NotFoundView(View):
    """Base Not Found/404 page object"""
    logo = GenericLocatorWidget(locator="//h1[@id='logo']")
    title = Text(locator='//*[@id="content"]/h1[2]')
    text_message = Text(locator='//*[@id="content"]/p')

    @property
    def is_displayed(self):
        return self.title.text == "Not Found" and \
               self.text_message.text == "Sorry. We can't find what you're looking for." and \
               self.logo.is_displayed
