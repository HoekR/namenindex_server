# Python server for scholarly web annotations

An experimental Python Flask server for the namenindex adapted from and modelled on Marijn Koolen's
```
git clone https://github.com/marijnkoolen/scholarly-web-annotation-server.git
```

The server uses [Elasticsearch](https://www.elastic.co/products/elasticsearch) for storage and retrieval of annotations. When running the SWA server, make sure you have a running Elasticsearch instance. Configuration of the Elasticsearch server is done in `settings.py`. This repository contains a file `settings-example.py` that shows how to configure the connection to Elasticsearch. Rename or copy this to `settings.py` to make sure the SWA server can read the configuration file.

## How to install

Clone the repository:
```
git clone https://github.com/xxx
```

Install the required python packages (for pipenv see https://docs.pipenv.org/):
```
pipenv install
```

## How to run

Start the server:
```
pipenv run python namen_server.py
```

and point your browser to `localhost:3000`

## How to modify

Run all tests:
```
make test_server
```
