# UI testing guide

## Configuration
First, you need to specify:
 * secrets in `secreets.yaml` or local version of secrets file
 * settings in in `settings.yaml` or local version of settings file

### Settings
In settings there are three options to run testsuite using option `source:`:
* `local` settings  will use webdrivers from library which refers to 
latest know webdrivers and store those webdrivers in cache/tmp folders
* `binary` settings will use binary files to run tests specified by `binary_path` variable
* `remote` settings will use containerized environment of  
[Selenium images](https://github.com/SeleniumHQ/docker-selenium)
    `remote_url` url and port for remote selenium webdriver instance, if not specified
`http://127.0.0.1:4444` will be used

    To run container use e.g. `podman run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" --rm
    selenium/standalone-chrome:latest` 

`webdriver:`:
Choose browser type -currently supported browsers options are `firefox`, `chrome`

`headless:`: Run UI tests in headless mode, options are `True/False` (About 30% faster option than classic run) - default is `True`. Use False setting for debugging or run observation


There can be also specified 3scale admin url which is used for browser 
navigation(by default is automatically fetched from dynaconf)
```yaml
threescale:
        admin:
            url: threescaleurl.example
```
     
Testsuite also can save screenshots to folder defined in env variable `resultsdir`
     
### Secrets
Contains  `username` and user `password` which is used for UI login into tenant

## Writing tests

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

### Views/Page objects
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
path_pattern = "/example/something"
```
Represents path pattern of View which will be converted to path using ids in parameterized paths

```python
def is_displayed(self):
        return self.first_example_element and self.seccond_example_element 
                and self.path in self.browser.url
```
Method check if elements are present on page and path is in current url.


### Widgets
Every page object is composed of widgets.
Most components can be used from widgetastic libraries, 
there you can find examples and usage(using selectors, actions etc.)
But there are also 3scale specific widgets/elements which have to be implemented separately or can be
inherited and changed.

3scale specified widgets are located in `testsuite/ui/widgets/__init__.py`

### Navigation

Navigator takes responsibility of navigation process during UI testing.
It uses two basic structures (prerequisites and steps) in order to construct logical path (or sequence of actions)
from root View to desired location. This simulates user actions during system navigation.

Navigation process consists of two parts:
   * 1. **Backtrace** - Views should extend NavigateStep class which defines simple method `prerequisite`.
        This method should specify View that is ancestor of accessible from(is navigable from).
        Backtrace process then create queue that consists of View sequence that describes path from root
        to desired View.
   * 2. **Perform of steps** - Sequentially pops Views from mentioned queue and invoke methods that are decorated
        as steps for navigation.

**Navigating to desired View**

Navigator class can navigate to desired view with two methods:
* **Navigator.navigate**  - perform navigation to specific View. If required by particular steps, args and kwargs
        should be specified. They are later passed to every step method and mapped to
        correct View parameters.
* Navigator.open - Directly opens desired View, by inserting its `path` in to browser url. (There is an optional argument `exact` which enables to open exact provided url.)

For more details see implementation.


### Conftest

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
  
###### Notice :
* UI tests which using login fixture should use decorator @pytest.mark.usefixtures("login")
  
See example
    
 ```python
def test_custom_login_example(navigator, custom_login, request):
    custom_login(name="test@example.com", password="password", finalizer_request=request)
    page = navigator.navigate(ExampleView)
```

* `navigator`

## Debugging

For debugging is recommended way to use [web_pdb](https://pypi.org/project/web-pdb/)
or built in debugger in PyCharm or another dev tool.

To stop the execution on specific point, the following statement can be added in the code:
```python
import web_pdb
web_pdb.set_trace()
```

After that you need to visit `localhost:5555` where is interactive console and other related information from debugger.

## Reporting

If a UI test fails, it will generate a screenshot from a moment, when the test was marked as failed. 
This is being handled by `pytest_exception_interact`. You can specify the output location by
setting `resultsdir` environmental variable or by passing an `--junitxml` argument (with path).
The name of a screenshot is fixed to `failed-test-screenshot.png`, the only thing that changes
is a directory, where we will save the screenshot in.

### Cases of reporting:

* if no option is selected, the `resultsdir` will be considered to be `.`. In this case, failing test `test1` 
  will put the screenshot into the `./attachments/ui/test1/` directory.


* `resultsdir=/home/tmp/` with failing test `test1` will put the screenshot into the 
  `/home/tmp/attachments/ui/test1/` directory.


* `--junitxml=/home/tmp/junit-ui-tests.xml` with failing test `test1` will put the screenshot in 
  `/home/tmp/attachments/junit-ui-tests/test1/` directory.
  

* `--junitxml=junit-ui-tests.xml` with failing test `test1` will put the screenshot in 
  `./attachments/junit-ui-tests/test1/` directory. The `.` in the path means that it will be saved in a starting location
  of a test (for example, if we run only a single test, this directory will be created in a same directory
  as a test is and if we for example start a test suite from `/home/tmp/`, the `.` will be replaced by `/home/tmp/`)


* if `--junitxml` and `resultsdir` is provided, the xml path will be used.

Note: If a test is parametrized, the output will be the same, except the test name will be set to its
failing variables (for example: `test1` with `param1` and `param2` will have the directory `test1[param1-param2]`) 
and not the `test1`.

## Example test 

```python
from testsuite.ui.views.admin import AccountsView, UsersView

def test_login(navigator, login, custom_login):
    page = navigator.navigate(UsersView)
    page.logout()
    custom_login(name="user", password="password")
    page2 = navigator.navigate(AccountsView)
    page2.do_action
```
