from fastapi import APIRouter, HTTPException, Query, Header, Depends, Request
from fastapi.responses import HTMLResponse

from dedi_registry.etc.enums import RecordStatus
from dedi_registry.database import Database, get_active_db
from .util import TEMPLATES


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
    :return: An HTML response with the home page content.
    """
    network_count = await db.networks.count(RecordStatus.ACTIVE)
    node_count = await db.networks.count_nodes(RecordStatus.ACTIVE)

    return TEMPLATES.TemplateResponse(
        'home.html',
        {
            'request': request,
            'page_title': 'Home | My Registry',
            'network_count': network_count,
            'node_count': node_count,
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
            'networks': networks,
            'network_status': network_status.value if network_status else None,
            'prev_url': prev_url,
            'next_url': next_url,
        }
    )
