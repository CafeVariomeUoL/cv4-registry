import hashlib
from uuid import UUID
from urllib.parse import urlparse, urlencode
from jsonpatch import JsonPatch
from fastapi import APIRouter, Query, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse

from dedi_registry.etc.enums import RecordStatus, RecordAction
from dedi_registry.database import Database, get_active_db
from dedi_registry.model.network import NetworkAudit, NetworkAuditRequestDetail
from .util import TEMPLATES, build_nav_links, get_request_detail, sanitise_next_url


admin_router = APIRouter(
    prefix='/admin',
    tags=['UI', 'Admin'],
)

_404_HTML = '404.html'
_404_TITLE = 'Network Not Found | Decentralised Discovery Network Registry'
_404_RETURN_LABEL = 'Back to Networks'


async def change_network_status(db: Database,
                                network_uuid: UUID,
                                request_detail: NetworkAuditRequestDetail,
                                new_status: RecordStatus,
                                ):
    """
    Change the status of a network (approve, reject, blacklist).
    :param db: The database instance to perform the operation.
    :param network_uuid: The UUID of the network to change status.
    :param request_detail: Details about the request for auditing purposes.
    """
    network = await db.networks.get(network_uuid)

    audits = await db.audits.get_network_audits(network_id=network_uuid)
    last_version = max((audit.version for audit in audits), default=0)
    old_json = network.model_dump()
    old_json_str = network.model_dump_json()
    network.status = new_status
    new_json = network.model_dump()
    new_json_str = network.model_dump_json()
    json_patch = JsonPatch.from_diff(old_json, new_json)

    await db.networks.update_status(
        network_id=network_uuid,
        new_status=new_status,
    )

    await db.audits.save(NetworkAudit(
        networkId=network_uuid,
        version=last_version + 1,
        action=RecordAction.APPROVE,
        actorNode='Administrator',
        patch=json_patch,
        hashBefore=f'sha256:{hashlib.sha256(old_json_str.encode()).hexdigest()}',
        hashAfter=f'sha256:{hashlib.sha256(new_json_str.encode()).hexdigest()}',
        requestDetail=request_detail
    ))


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
    next_url = sanitise_next_url(next_url)

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
                           next_url: str | None = Form(None, alias='next'),
                           ):
    """
    Handle admin login form submission.
    \f
    :return:
    """
    next_url = sanitise_next_url(next_url)

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


@admin_router.post('/networks/{network_id}/approve')
async def approve_network_registration(request: Request,
                                       network_id: str,
                                       db: Database = Depends(get_active_db),
                                       request_detail: NetworkAuditRequestDetail = Depends(get_request_detail),
                                       ):
    """
    Approve a network registration request.
    """
    if not request.session.get('username', None):
        return RedirectResponse(
            request.url_for('get_admin_login_page', next=request.url.path),
            status_code=status.HTTP_303_SEE_OTHER
        )

    network_uuid = UUID(network_id)
    network = await db.networks.get(network_uuid)

    if not network:
        return TEMPLATES.TemplateResponse(
            _404_HTML,
            {
                'request': request,
                'page_title': _404_TITLE,
                'detail': f'Network with ID {network_id} not found.',
                'return_url': request.url_for('display_networks'),
                'return_label': _404_RETURN_LABEL,
                'nav_links': await build_nav_links(request, db),
            },
            status_code=404,
        )

    if network.status == RecordStatus.ACTIVE:
        return RedirectResponse(
            request.url_for('display_network_detail', network_id=network_id),
            status_code=status.HTTP_303_SEE_OTHER
        )

    await change_network_status(db, network_uuid, request_detail, RecordStatus.ACTIVE)

    return RedirectResponse(
        request.url_for('display_network_detail', network_id=network_id),
        status_code=status.HTTP_303_SEE_OTHER
    )


@admin_router.post('/networks/{network_id}/reject')
async def reject_network_registration(request: Request,
                                      network_id: str,
                                      db: Database = Depends(get_active_db),
                                      request_detail: NetworkAuditRequestDetail = Depends(get_request_detail),
                                      ):
        """
        Reject a network registration request.
        """
        if not request.session.get('username', None):
            return RedirectResponse(
                request.url_for('get_admin_login_page', next=request.url.path),
                status_code=status.HTTP_303_SEE_OTHER
            )

        network_uuid = UUID(network_id)
        network = await db.networks.get(network_uuid)

        if not network:
            return TEMPLATES.TemplateResponse(
                _404_HTML,
                {
                    'request': request,
                    'page_title': _404_TITLE,
                    'detail': f'Network with ID {network_id} not found.',
                    'return_url': request.url_for('display_networks'),
                    'return_label': _404_RETURN_LABEL,
                    'nav_links': await build_nav_links(request, db),
                },
                status_code=404,
            )

        if network.status == RecordStatus.REJECTED:
            return RedirectResponse(
                request.url_for('display_network_detail', network_id=network_id),
                status_code=status.HTTP_303_SEE_OTHER
            )

        await change_network_status(db, network_uuid, request_detail, RecordStatus.REJECTED)

        return RedirectResponse(
            request.url_for('display_network_detail', network_id=network_id),
            status_code=status.HTTP_303_SEE_OTHER
        )


@admin_router.post('/networks/{network_id}/blacklist')
async def blacklist_network(request: Request,
                            network_id: str,
                            db: Database = Depends(get_active_db),
                            request_detail: NetworkAuditRequestDetail = Depends(get_request_detail),
                            ):
    """
    Blacklist a network.
    """
    if not request.session.get('username', None):
        return RedirectResponse(
            request.url_for('get_admin_login_page', next=request.url.path),
            status_code=status.HTTP_303_SEE_OTHER
        )

    network_uuid = UUID(network_id)
    network = await db.networks.get(network_uuid)

    if not network:
        return TEMPLATES.TemplateResponse(
            _404_HTML,
            {
                'request': request,
                'page_title': _404_TITLE,
                'detail': f'Network with ID {network_id} not found.',
                'return_url': request.url_for('display_networks'),
                'return_label': _404_RETURN_LABEL,
                'nav_links': await build_nav_links(request, db),
            },
            status_code=404,
        )

    if network.status == RecordStatus.BLACKLISTED:
        return RedirectResponse(
            request.url_for('display_network_detail', network_id=network_id),
            status_code=status.HTTP_303_SEE_OTHER
        )
    await change_network_status(db, network_uuid, request_detail, RecordStatus.BLACKLISTED)
    return RedirectResponse(
        request.url_for('display_network_detail', network_id=network_id),
        status_code=status.HTTP_303_SEE_OTHER
    )
