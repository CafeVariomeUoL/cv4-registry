import secrets
from pydantic import Field, ConfigDict
from fastapi import APIRouter, HTTPException, Query, Depends, status

from dedi_registry.etc.consts import LOGGER
from dedi_registry.etc.enums import DatabaseConfigType
from dedi_registry.etc.utils import validate_hash_challenge
from dedi_registry.cache import Cache, get_active_cache
from dedi_registry.database import Database, get_active_db
from dedi_registry.model.base import JsonModel
from dedi_registry.model.network import Network, NetworkAuditRequestDetail, NetworkAudit


network_router = APIRouter(
    prefix='/networks',
    tags=['Network'],
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


@network_router.get('/challenge', response_model=ChallengeResponse)
async def get_challenge(cache: Cache = Depends(get_active_cache),
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


@network_router.post('', response_model=Network, status_code=status.HTTP_201_CREATED)
async def register_network(network: Network,
                           nonce: str = Query(..., description='The nonce received from the challenge endpoint'),
                           solution: str = Query(..., description='The challenge solution'),
                           db: Database = Depends(get_active_db),
                           cache: Cache = Depends(get_active_cache),
                           ):
    """
    Register a new network in the system.
    \f
    :param network: The network details to register.
    :param nonce: The nonce received from the challenge endpoint to validate the request.
    :param solution: The challenge solution to validate the request.
    :param db: The database instance to store the network.
    :param cache: The cache instance to retrieve the challenge for validation.
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

    await db.networks.save(network)
