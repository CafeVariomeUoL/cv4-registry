import secrets
import hashlib
from uuid import UUID
import jsonpatch
from pydantic import Field, ConfigDict
from fastapi import APIRouter, HTTPException, Query, Header, Depends, status

from dedi_registry.etc.consts import LOGGER, CONFIG
from dedi_registry.etc.enums import DatabaseConfigType, RecordAction, RecordStatus
from dedi_registry.etc.utils import validate_hash_challenge
from dedi_registry.cache import Cache, get_active_cache
from dedi_registry.database import Database, get_active_db
from dedi_registry.model.base import JsonModel
from dedi_registry.model.network import Network, NetworkAuditRequestDetail, NetworkAudit
from .util import get_request_detail


api_router = APIRouter(
    prefix='/api',
    tags=['API'],
)


class ChallengeResponse(JsonModel):
    """
    A data transfer object for the response with a hash challenge.
    """

    model_config = ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
    )

    nonce: str = Field(
        ...,
        description='A random nonce to be used in the challenge',
    )
    difficulty: int = Field(
        ...,
        description='The difficulty level of the challenge',
    )


@api_router.get('/v1/challenge', response_model=ChallengeResponse)
async def get_challenge_v1(cache: Cache = Depends(get_active_cache),
                           db: Database = Depends(get_active_db),
                           ):
    """
    Generate a Proof of Work challenge for request validation.

    This is to prevent spam and abuse of the unprotected endpoints by enforcing a
    CPU cost for each request.
    \f
    :param cache: The cache instance to store the challenge.
    :param db: The database instance to retrieve configuration settings.
    :return: The nonce and difficulty level for the challenge.
    """
    nonce = secrets.token_hex(16)
    security_config = await db.config.get_config(DatabaseConfigType.SECURITY)
    difficulty = security_config.base_difficulty + security_config.difficulty_shift

    LOGGER.debug(
        'Generating challenge with nonce: %s, difficulty: %d',
        nonce,
        difficulty
    )

    await cache.challenge.save_challenge(
        nonce=nonce,
        difficulty=difficulty
    )

    return ChallengeResponse(
        nonce=nonce,
        difficulty=difficulty
    )


@api_router.post('/v1/networks', response_model=Network, status_code=status.HTTP_201_CREATED)
async def register_network_v1(network: Network,
                              nonce: str = Query(..., description='The nonce received from the challenge endpoint'),
                              solution: str = Query(..., description='The challenge solution'),
                              sender_node: str = Header(
                                  ...,
                                  alias='Node-ID', description='The ID of the node sending the request'
                              ),
                              db: Database = Depends(get_active_db),
                              cache: Cache = Depends(get_active_cache),
                              request_detail: NetworkAuditRequestDetail = Depends(get_request_detail),
                              ):
    """
    Register a new network in the system.
    \f
    :param network: The network details to register.
    :param nonce: The nonce received from the challenge endpoint to validate the request.
    :param solution: The challenge solution to validate the request.
    :param sender_node: The ID of the node sending the request.
    :param db: The database instance to store the network.
    :param cache: The cache instance to retrieve the challenge for validation.
    :param request_detail: Details about the request for auditing purposes.
    :return: The registered network details.
    """
    challenge_difficulty = await cache.challenge.get_challenge(nonce)

    if not challenge_difficulty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid or expired challenge nonce.'
        )

    if not validate_hash_challenge(nonce, challenge_difficulty, solution):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Invalid challenge solution.'
        )

    existing_network = await db.networks.get(network.network_id)

    if existing_network:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Network with ID {network.network_id} already exists.'
        )

    node_found = False
    sender_uuid = UUID(sender_node)
    for node in network.nodes:
        if node.node_id == sender_uuid:
            node_found = True
            break

    if not node_found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Sender node is not part of the network being registered.'
        )

    if CONFIG.auto_approve:
        network.status = RecordStatus.ACTIVE
    else:
        network.status = RecordStatus.PENDING

    await db.networks.save(network)

    json_dump = network.model_dump()
    json_patch = jsonpatch.JsonPatch.from_diff({}, json_dump)

    audit_record = NetworkAudit(
        networkId=network.network_id,
        version=0,
        action=RecordAction.CREATE,
        actorNode=sender_uuid,
        patch=json_patch,
        hashAfter=f'sha256:{hashlib.sha256(json_dump.encode()).hexdigest()}',
        requestDetail=request_detail
    )

    await db.audits.save(audit_record)

    LOGGER.info(
        'Registered new network with ID %s by node %s',
        network.network_id,
        sender_node
    )
    LOGGER.debug('Network details: %s', network.model_dump_json())

    return network
