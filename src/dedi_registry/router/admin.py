from urllib.parse import urlparse, urlencode
from fastapi import APIRouter, Query, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from dedi_registry.database import Database, get_active_db
from .util import TEMPLATES, build_nav_links


admin_router = APIRouter(
    prefix='/admin',
    tags=['UI', 'Admin'],
)


@admin_router.get('/login', response_class=HTMLResponse)
async def get_admin_login_page(request: Request,
                               next_url: str | None = Query(None, alias="next"),
                               db: Database = Depends(get_active_db)
                               ):
    """
    Serve the admin login page.
    \f
    :param request: Request object.
    :param next_url: The URL to redirect to after successful login.
    :param db: The database instance to retrieve user information.
    :return: An HTML response with the admin login page content.
    """
    if request.session.get('username', None):
        # If already logged in, redirect to the dashboard or next_url
        redirect_url = next_url or request.url_for('get_admin_dashboard')
        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return TEMPLATES.TemplateResponse(
        'admin_login.html',
        {
            'request': request,
            'page_title': 'Admin Login | Decentralised Discovery Network Registry',
            'login_action': request.url_for('post_admin_login'),
            'next_url': next_url or request.url_for('get_admin_dashboard'),
            'error': request.query_params.get('error', None),
            'nav_links': await build_nav_links(request, db),
        }
    )


@admin_router.post('/login', response_class=RedirectResponse)
async def post_admin_login(request: Request,
                           db: Database = Depends(get_active_db),
                           username: str = Form(...),
                           password: str = Form(...),
                           next_url: str | None = Form(None),
                           ):
    """
    Handle admin login form submission.
    \f
    :return:
    """
    def login_redirect(error: str | None = None):
        params = {}
        if error:
            params['error'] = error

        if next_url:
            params['next'] = next_url

        url = request.url_for('get_admin_login_page')

        if params:
            url = f'{url}?{urlencode(params)}'

        return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)

    if not username or not password:
        return login_redirect('Please enter username or password correctly')

    user = await db.users.get(username)

    if not user:
        return login_redirect('Invalid username or password')

    if not user.validate_password(password):
        return login_redirect('Invalid username or password')

    request.session['username'] = user.username

    def is_safe_relative_path(u: str) -> bool:
        try:
            p = urlparse(u)

            return (not p.scheme and not p.netloc and u.startswith('/')) and (u != request.url.path)
        except Exception:
            return False

    if next_url and is_safe_relative_path(next_url):
        dest = next_url
    else:
        dest = '/'

    return RedirectResponse(dest, status_code=status.HTTP_303_SEE_OTHER)


@admin_router.get('/logout')
async def admin_logout(request: Request):
    """
    Logout a user
    :param request: Request object
    :return: Redirection to the login page
    """
    request.session.clear()

    return RedirectResponse(request.url_for('get_admin_login_page'), status_code=status.HTTP_303_SEE_OTHER)


@admin_router.get('')
async def get_admin_dashboard():
    """
    Serve the admin dashboard page.
    \f
    :return: An HTML response with the admin dashboard content.
    """
