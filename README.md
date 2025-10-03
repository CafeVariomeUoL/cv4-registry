# Cafe Variome V4 Network Registry

A network registry for Cafe Variome V4 systems to report the networks for public finding. Forked from [Decentralised Discovery Network Registry](https://github.com/Firefox2100/dedi-registry).

## Features

This is a simple registry service that allows CV4 systems to register their networks. The CV4 servers are running independently, without a place to control what networks are there and how to join or find them. This service fills in the blanks by allowing the nodes running the CV4 software to optionally report the network information to the registry, so that the others can easily find and join the networks.

The system offers:

- **Network Registration**: CV4 nodes can register their networks with details such as network name, description, and connection information.
- **Network Discovery**: Users can search and discover registered networks based on various criteria.
- **API Access**: Provides a RESTful API for programmatic access to register and discover
- **Admin Controlling**: An admin may choose to manually approve or automatically approve a network registration. Later, they may decide to reject the registration anyway (which will remove it from the public listing), or ban the network permanently (which bans the registration of the same IP address, domain and user agent in the future).
- **Security on Registration**: To prevent spam and abuse, the registration process includes a hash challenge to be solved by the registering node. The challenge solving function is implemented in the gateway software itself, and SHOULD be implemented by any other software that uses the same protocol stack.
- **Security on Modification**: When modifying the network information, for example by reporting new nodes, change of name or description, etc. the request needs to be signed by a private key. The public key should have been reported during the registration. This also serves as permission control, as it's a network management key, and may be controlled by one or more nodes in the network that was given the permission to manage the network.

## Installation

The software is written in Python and uses the FastAPI framework with Jinja2 for UI rendering. It can be run using Uvicorn.

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- MongoDB 8.0 or higher
- Redis 7.0 or higher

### Installing from code

Ensure you have Python environment setup. We recommend using either a separate conda environment or `venv` or `virtualenv` to create a virtual environment. This way the installation is cleaner and easier to manage.

```bash
git clone https://github.com/Firefox2100/dedi-registry.git
cd dedi-registry
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install . # or `pip install -e .` for editable install
```

The software is configured via environment variables. It also can read a `.env` file in a given path, defaulting to `./conf/.env`. The path to that file is configurable via the `DR_ENV_FILE` environment variable.

```bash
cp example.env conf/.env
vim conf/.env  # Edit the configuration as needed
export DR_ENV_FILE=/absolute/path/to/conf/.env  # Optional, if you want to start from a different working directory. You can also keep this in your shell profile for convenience.
```

Assuming you have started the databases as needed and configured them correctly, the service is ready to start. You can start it using Uvicorn:

```bash
uvicorn dedi_registry.asgi:application --host 0.0.0.0 --port 5000 --log-config conf/uvicorn-log.config.yaml
```

Or, the `pip install` earlier should have installed a `dedi-registry` command that is available as long as the Python environment is activated:

```bash
dedi-registry
```

Note that this is for convenient startup in self-contained environments. None of the startup parameters are configurable via command line arguments, including worker counts.

### Running with Docker

The software can also be run using Docker. A `Dockerfile` is provided for building the image. A copy of the image is also published on [Docker Hub](https://hub.docker.com/r/firefox2100/dedi-registry). Refer to the documents there for tags and versions.

To build the Docker image locally (assuming already in the project directory):

```bash
docker build -t brookeslab/cv4-registry:local .
```

An example docker compose file is provided in the repository as a starting point. You may need to adjust the environment variables and volume mounts as needed.

## Configuration

The software is configured via environment variables. A sample configuration file is provided as `example.env`. You can copy it to `conf/.env` and edit it as needed. Some security sensitive values are not listed in it, and you should generate them yourself.

| Variable           | Description                                               | Default Value |
|--------------------|-----------------------------------------------------------|---------------|
| DR_ENV_FILE        | Path to the .env file                                     | ./conf/.env   |
| DR_AUTO_APPROVE    | Whether to automatically approve network registrations    | false         |
| DR_ALLOW_ORIGINS   | List of allowed origins for CORS                          | []            |
| DR_DATABASE_DRIVER | Database driver to use (mongo)                            | mongo         |
| DR_MONGODB_HOST    | MongoDB host                                              | localhost     |
| DR_MONGODB_PORT    | MongoDB port                                              | 27017         |
| DR_MONGODB_DB_NAME | MongoDB database name                                     | ddn-registry  |
| DR_CACHE_DRIVER    | Cache driver to use (redis)                               | redis         |
| DR_REDIS_HOST      | Redis host                                                | localhost     |
| DR_REDIS_PORT      | Redis port                                                | 6379          |
| DR_LOGGING_LEVEL   | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)     | INFO          |
| DR_USE_HTTPS       | Whether the service is behind an HTTPS proxy              | true          |
| DR_ADMIN_USERNAME  | Initial admin username. Using CLI is recommended instead. | None          |
| DR_ADMIN_PASSWORD  | Initial admin password. Using CLI is recommended instead. | None          |

## Licences and Third-Party Libraries

The software itself is licensed under MIT. See the [LICENSE](LICENSE) file for details. The upstream project is licensed under GPLv3.0 or later. This fork has obtained permissions from the original author to re-license under MIT.

The software uses several third-party libraries, but does not re-distribute most of them. The ones that are bundled and re-distributed are:

- Bootstrap 5.3.8 (MIT License)

Their licences are included with their respective files or source directories.
