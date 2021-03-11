# UI testing guide

## Before You Run It

###Configuration
First, you need to specify:
 * secrets in `secreets.yaml` or local version of secrets file
 * settings in in `settings.yaml` or local version of settings file

####Settings
In settings there are two options to run testsuite using option `provider:`:
* `local` settings  will use webdrivers from library which refers to 
latest know webdrivers and store those webdrivers in cache/tmp folders
* `remote` settings will use containerized environment of  
[Selenium images](https://github.com/SeleniumHQ/docker-selenium)
* `remote_url` url and port for remote selenium webdriver instance, if not specified
`http://127.0.0.1:4444` will be used

    To run container use e.g. `podman run -d -p 4444:4444 -p 5900:5900 -v /dev/shm:/dev/shm 
    selenium/standalone-chrome:4.0.0-beta-1-20210215` 

Currently supported browsers options are `firefox`, `chrome` and `edge`
(edge only for remote webdriver or using binary path)

There can be also specified 3scale admin url which is used for browser 
navigation(by default is automatically fetched from dynaconf)
```yaml
threescale:
        admin:
            url: threescaleurl.example
```
     
Testsuite also can save screenshots to folder defined in env variable `resultsdir`
     
####Secrets
Contains  `username` and user `password` which is used for UI login into tenant

###Writing tests

We use Widgetastic library for developing our tests. 
Widgetastic contains following separated repository dependant on used UI technology:
* [Widgetastic.core](https://github.com/RedHatQE/widgetastic.core)  basic elements
* [Widgetastic.paternfly](https://github.com/RedHatQE/widgetastic.patternfly) using PFv3
* [Widgetastic.paternfly4](https://github.com/RedHatQE/widgetastic.patternfly4) using PFv4

If you need to use element which is not included in `widgetastic.paternfly4`, but is based on [PF4] 
the best solution will be create that component and send PR to 
[Widgetastic.paternfly4 repository](https://github.com/RedHatQE/widgetastic.patternfly4). 
This may help other teams and speed up development of library.

At first you need to create page objects for handling elements on page, 
then specify navigation to desired page and after that you can write tests with some expectations.

####Views/Page objects
We have 4 basic Views in Admin portal, from these views should inherit  all other views. 
* `AudienceView` - audience menu contains
* `ProductView` - product specific menu
* `BackendView` - backend specific menu
* `AccountSettingsView` - tenant settings specific menu
Each of this views groups views with same menus.

All basic views (except specific like Wizzard or Login page) inherits from `BaseAdminView` Class 
which is top view and contains 3scale header menu.

Every view should have following attributes and methods
```python
ROOT = ".//div[contains(@class, ExampleRootElement)]"
```
Represents Root element for faster element search

```python
endpoint_path = "/example/something"
```
Represents endpoint path of View

```python
def is_displayed(self):
        return self.first_example_element and self.seccond_example_element 
                and self.endpoint_path in self.browser.url
```
Method check if elements are present on page and endpoint_path is in current url.


####Widgets
Every page object is composed from widgets.
Most components can be used from widgetastic libraries, 
there you can find examples and usage(using selectors, actions etc.)
But there are also 3scale specific widgets/elements which have to be implemented separately or can be
inherited and changed.

3scale specified widgets are located in `testsuite/ui/widgets/__init__.py`

####Navigation

####Conftest

* `browser` - represents browser instance with admin portal address  
which can be passed to View and make tweaks
   
* `custom_browser` - represents browser instance which can be passed to View and make tweaks
   
    param: `url=None` can override default url which will be used

* `login` - Do basic login using `username` and `password` variable. If not provided 
credentials from secret file will be used.

* `custom_login` Do login with provided credentials.

    param: `name=None` username for login
    
    param: `password=None` password for login
    
    param: `finalizer_request=None` can override default finalizer which is invoked at the end of the
    fixture scope, if not set default scope (module) will be applied
    
    See example
    
 ```python
def test_custom_login_example(navigator, custom_login, request):
    custom_login(name="test@example.com", password="password", finalizer_request=request)
    page = navigator.navigate(ExampleView)
```

* `navigator`

###Debugging

For debugging is recommended way to use [web_pdb](https://pypi.org/project/web-pdb/)
Using other debuggers like built in debugger in PyCharm may cause unexpected results.

To stop the execution on specific point, the following statement can be added in the code:
```python
import web_pdb
web_pdb.set_trace()
```

After that you need to visit `localhost:5555` where is interactive console and other related information from debugger.

###Example test 

```python
from testsuite.ui.views.admin import AccountsView, UsersView

def test_login(navigator, login, custom_login):
    page = navigator.navigate(UsersView)
    page.logout()
    custom_login(name="user", password="password")
    page2 = navigator.navigate(AccountsView)
    page2.do_action
```
