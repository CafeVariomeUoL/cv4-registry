from uuid import UUID
from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import HTMLResponse

from dedi_registry.etc.enums import RecordStatus
from dedi_registry.database import Database, get_active_db
from .util import TEMPLATES, build_nav_links


ui_router = APIRouter(
    tags=['UI'],
)


@ui_router.get('/', response_class=HTMLResponse)
async def get_home_page(request: Request,
                        db: Database = Depends(get_active_db),
                        ):
    """
    Serve the home page of the Decentralised Discovery Network Registry.
    \f
    :param request: Request object.
    :param db: Database instance.
    :return: An HTML response with the home page content.
    """
    network_count = await db.networks.count(RecordStatus.ACTIVE)
    node_count = await db.networks.count_nodes(RecordStatus.ACTIVE)
    nav_links = await build_nav_links(request, db)

    return TEMPLATES.TemplateResponse(
        'home.html',
        {
            'request': request,
            'page_title': 'Home | Decentralised Discovery Network Registry',
            'network_count': network_count,
            'node_count': node_count,
            'nav_links': nav_links,
        }
    )


@ui_router.get('/networks', response_class=HTMLResponse)
async def display_networks(request: Request,
                           network_status: RecordStatus = Query(
                               None,
                               description='Filter networks by their status'
                           ),
                           cursor_id: str | None = Query(
                               None,
                               description='The ID of the last network from the previous page for pagination'
                           ),
                           limit: int = Query(
                               10,
                               ge=0,
                               le=100,
                               description='The maximum number of records to return. 0 for no limit.'
                           ),
                           forward: bool = Query(
                               True,
                               description='Direction of pagination. True for forward, False for backward.'
                           ),
                           db: Database = Depends(get_active_db),
                           ):
    """
    Display a list of networks with optional filtering and pagination.
    \f
    :param request: Request object.
    :param network_status: Optional status to filter networks by.
    :param cursor_id: Optional ID of the last network from the previous page for pagination.
    :param limit: Maximum number of records to return. 0 for no limit.
    :param forward: Direction of pagination. True for forward, False for backward.
    :param db: Database instance.
    :return: An HTML response with the list of networks.
    """
    networks, first_cursor_id, last_cursor_id = await db.networks.filter(
        status=network_status,
        cursor_id=cursor_id,
        limit=limit,
        forward=forward,
    )

    show_prev = cursor_id is not None
    show_next = last_cursor_id is not None

    def build_url(new_cursor_id: str | None, new_forward: bool) -> str:
        params = {
            'cursor_id': new_cursor_id,
            'limit': limit,
            'forward': str(new_forward).lower(),
        }

        if network_status is not None:
            params['network_status'] = network_status.value

        base = '/networks?'
        query = '&'.join(f'{key}={value}' for key, value in params.items() if value is not None)
        return base + query

    prev_url = build_url(first_cursor_id, False) if show_prev else None
    next_url = build_url(last_cursor_id, True) if show_next else None

    return TEMPLATES.TemplateResponse(
        'networks.html',
        {
            'request': request,
            'page_title': 'Networks | Decentralised Discovery Network Registry',
            'networks': networks,
            'network_status': network_status.value if network_status else None,
            'prev_url': prev_url,
            'next_url': next_url,
            'nav_links': await build_nav_links(request, db),
        }
    )


@ui_router.get('/networks/{network_id}', response_class=HTMLResponse)
async def display_network_detail(request: Request,
                                 network_id: str,
                                 db: Database = Depends(get_active_db),
                                 ):
    """
    Display detailed information about a specific network.
    \f
    :param request: Request object.
    :param network_id: The ID of the network to display.
    :param db: Database instance.
    :return: An HTML response with the network details.
    """
    try:
        network_uuid = UUID(network_id, version=4)
    except ValueError:
        return TEMPLATES.TemplateResponse(
            '404.html',
            {
                'request': request,
                'page_title': 'Network Not Found | Decentralised Discovery Network Registry',
                'detail': f'Invalid network ID format: {network_id}',
                'return_url': request.url_for('display_networks'),
                'return_label': 'Back to Networks',
                'nav_links': await build_nav_links(request, db),
            },
            status_code=404,
        )
    network = await db.networks.get(network_uuid)

    if not network:
        return TEMPLATES.TemplateResponse(
            '404.html',
            {
                'request': request,
                'page_title': 'Network Not Found | Decentralised Discovery Network Registry',
                'detail': f'Network with ID {network_id} not found.',
                'return_url': request.url_for('display_networks'),
                'return_label': 'Back to Networks',
                'nav_links': await build_nav_links(request, db),
            },
            status_code=404,
        )

    network_audits = await db.audits.get_network_audits(network_uuid)

    audit_view = []
    for audit in network_audits or []:
        audit_view.append({
            'version': audit.version,
            'action': audit.action.value,
            'actor': str(audit.actor_node),
            'timestamp': audit.timestamp.isoformat(),
            'hash_before': audit.hash_before,
            'hash_after': audit.hash_after,
            'request_detail': {
                'ip_address': audit.request_detail.ip_address,
                'user_agent': audit.request_detail.user_agent,
            },
            'patch': audit.patch or [],
        })

    return TEMPLATES.TemplateResponse(
        'network_detail.html',
        {
            'request': request,
            'page_title': f'Network {network.network_name} | Decentralised Discovery Network Registry',
            'network': {
                'network_id': str(network.network_id),
                'network_name': network.network_name,
                'description': network.description,
                'status': network.status.value,
                'public_key': network.public_key,
                'nodes': [
                    {
                        'url': node.url,
                        'name': node.node_name,
                        'description': node.description,
                        'public_key': node.public_key,
                    } for node in network.nodes or []
                ]
            },
            'network_status': network.status.value,
            'audits': audit_view,
            'nav_links': await build_nav_links(request, db),
        }
    )
