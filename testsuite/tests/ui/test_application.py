"""Rewrite of spec/ui_specs/create_application_spec.rb"""

from testsuite import rawobj
from testsuite.ui.views.admin.audience.application import ApplicationEditView
from testsuite.utils import blame


# pylint: disable=too-many-arguments
def test_application_create(service, custom_app_plan, custom_ui_application, account, request, api_client):
    """
    Preparation:
        - Create custom application plan
        - Create custom application
    Test if:
        - application has correct name
        - application has correct description
        - application has correct application plan
        - application has correct account
        - response has status code 200
    """
    name = blame(request, "ui_account")
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_ui_application(name, "description", plan, account)

    assert app["name"] == name
    assert app["description"] == "description"
    assert app["plan_id"] == plan.entity_id
    assert app["account_id"] == account.entity_id
    response = api_client(app).get("/")
    assert response.status_code == 200


# pylint: disable=unused-argument
def test_application_update(login, application, account, service, navigator):
    """
    Preparation:
        - Create custom application plan
        - Create custom application
        - Edit application
    Test if:
        - application has edited name
        - application has edited description
    """
    app_edit = navigator.navigate(ApplicationEditView, application=application, product=service)
    app_edit.update("updated_name", "updated_description")
    app = account.applications.read(application.entity_id)

    assert app["name"] == "updated_name"
    assert app["description"] == "updated_description"


# pylint: disable=too-many-arguments
def test_application_delete(service, custom_app_plan, custom_ui_application, account, request, navigator):
    """
    Preparation:
        - Create custom application plan
        - Create custom application
        - Delete application
    Test if:
        - application no longer exists
    """
    name = blame(request, "ui_account")
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_ui_application(name, "description", plan, account, autoclean=False)

    application = navigator.navigate(ApplicationEditView, application=app, product=service)
    application.delete()
    app = account.applications.read_by_name(app["name"])

    assert app is None
