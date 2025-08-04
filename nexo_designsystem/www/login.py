import frappe
from frappe import _
from frappe.utils import cint
from frappe.auth import LoginManager
from frappe.utils.oauth import get_oauth2_authorize_url, get_oauth_keys
import json

no_cache = 1

def get_context(context):
    # Redirect if already logged in
    if frappe.session.user != "Guest":
        frappe.local.flags.redirect_location = "/app"
        raise frappe.Redirect

    context.no_breadcrumbs = True
    context.title = _("Login to NEXO ERP")

    # Check if there's a message to show
    if frappe.form_dict.get('message'):
        context.message = frappe.form_dict.get('message')
        context.indicator_color = frappe.form_dict.get('indicator_color', 'info')

    return context

@frappe.whitelist(allow_guest=True)
def login():
    try:
        login_manager = LoginManager()
        login_manager.authenticate(
            user=frappe.form_dict.get('usr'),
            pwd=frappe.form_dict.get('pwd')
        )
        login_manager.post_login()

        if frappe.response.get("message") == "Logged In":
            frappe.response["home_page"] = "/app"

            # Handle different response formats
            if frappe.local.request.headers.get("Content-Type") == "application/json":
                frappe.response["message"] = "Logged In"
            else:
                # Redirect for form submission
                frappe.local.flags.redirect_location = "/app"
                raise frappe.Redirect

    except frappe.exceptions.AuthenticationError as e:
        frappe.clear_messages()
        frappe.local.response["message"] = _("Invalid login credentials")
        frappe.local.response["exc_type"] = "AuthenticationError"
        frappe.local.response["http_status_code"] = 401

        if frappe.local.request.headers.get("Content-Type") != "application/json":
            # Redirect back to login with error message
            frappe.local.flags.redirect_location = f"/login?message={frappe.local.response['message']}&indicator_color=danger"
            raise frappe.Redirect

    except Exception as e:
        frappe.log_error(f"Login error: {str(e)}")
        frappe.local.response["message"] = _("An error occurred during login. Please try again.")
        frappe.local.response["http_status_code"] = 500

        if frappe.local.request.headers.get("Content-Type") != "application/json":
            frappe.local.flags.redirect_location = f"/login?message={frappe.local.response['message']}&indicator_color=danger"
            raise frappe.Redirect