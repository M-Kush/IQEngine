# vim: tabstop=4 shiftwidth=4 expandtab


import os

from database.models import Metadata

test_datasource = {
    "name": "name",
    "account": "account",
    "container": "container",
    "description": "description",
}

test_datasource_id = f'{test_datasource["account"]}_{test_datasource["container"]}'

valid_metadata = {
    "global": {
        "core:datatype": "string",
        "core:sample_rate": 1,
        "core:version": "1.0.0",
    },
    "captures": [
        {
            "core:sample_start": 1,
        }
    ],
    "annotations": [
        {
            "core:sample_start": 1,
            "core:sample_count": 1,
        }
    ],
}


def test_api_get_config(client):
    os.environ["DETECTOR_ENDPOINT"] = "http://localhost:5000"
    os.environ["CONNECTION_INFO"] = "connection_info"
    os.environ["GOOGLE_ANALYTICS_KEY"] = "google_analytics_key"
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == {
        "detectorEndpoint": "http://localhost:5000",
        "connectionInfo": "connection_info",
        "googleAnalyticsKey": "google_analytics_key",
    }


def test_api_returns_ok(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == "OK"


# This test no longer valid as URL will never be valid with made up account and container
def test_api_post_meta_bad_datasource_id(client):
    response = client.post(
        "/api/datasources/nota/validid/file_path/meta", json=valid_metadata
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Datasource not found"}


def test_api_post_meta_missing_datasource(client):
    source_id = "madeup/datasource"
    response = client.post(
        f"/api/datasources/{source_id}/file_path/meta", json=valid_metadata
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Datasource not found"}


def test_api_post_meta(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 201
    metadata = Metadata.parse_obj(response.json())
    assert metadata.globalMetadata.traceability_revision == 0
    assert metadata.globalMetadata.traceability_origin == {
        "account": test_datasource["account"],
        "container": test_datasource["container"],
        "file_path": "file_path",
    }
    assert (
        metadata.annotations[0].core_sample_start
        == valid_metadata["annotations"][0]["core:sample_start"]
    )
    assert (
        metadata.annotations[0].core_sample_count
        == valid_metadata["annotations"][0]["core:sample_count"]
    )
    assert (
        metadata.captures[0].core_sample_start
        == valid_metadata["captures"][0]["core:sample_start"]
    )


def test_api_post_existing_meta(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Metadata already exists"}


def test_api_put_meta(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 201
    response = client.put(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 204


def test_api_put_meta_not_existing(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.put(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 404


def test_api_get_meta(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta',
        json=valid_metadata,
    )
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta'
    )
    assert response.status_code == 200


def test_api_get_meta_not_existing(client):
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta'
    )
    assert response.status_code == 404  # Because the datasource doesn't exist
    client.post("/api/datasources", json=test_datasource).json()
    response = client.get(
        '/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file_path/meta'
    )
    assert response.status_code == 404  # Because the metadata doesn't exist


def test_api_get_all_meta(client):
    client.post("/api/datasources", json=test_datasource).json()
    client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/record_a/meta',
        json=valid_metadata,
    )
    client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/record_b/meta',
        json=valid_metadata,
    )
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/meta'
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_api_create_datasource(client):
    response = client.post("/api/datasources", json=test_datasource)
    assert response.status_code == 201


def test_api_get_datasources(client):
    response = client.get("/api/datasources")
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = client.post("/api/datasources", json=test_datasource)
    response = client.get("/api/datasources")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_api_filename_url_encoded(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file%2Fpath/meta',
        json=valid_metadata,
    )
    assert response.status_code == 201
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file%2Fpath/meta'
    )
    assert response.status_code == 200
    response_object = response.json()
    assert (
        response_object["global"]["traceability:origin"]["account"]
        == test_datasource["account"]
    )
    assert (
        response_object["global"]["traceability:origin"]["container"]
        == test_datasource["container"]
    )
    assert response_object["global"]["traceability:origin"]["file_path"] == "file/path"


def test_api_filename_non_url_encoded(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file/path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 201
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file/path/meta'
    )
    assert response.status_code == 200
    response_object = response.json()
    assert (
        response_object["global"]["traceability:origin"]["account"]
        == test_datasource["account"]
    )
    assert (
        response_object["global"]["traceability:origin"]["container"]
        == test_datasource["container"]
    )
    assert response_object["global"]["traceability:origin"]["file_path"] == "file/path"
    assert response_object["global"]["traceability:revision"] == 0


def test_api_update_file_version(client):
    client.post("/api/datasources", json=test_datasource).json()
    response = client.post(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file/path/meta',
        json=valid_metadata,
    )
    assert response.status_code == 201
    new_metadata = valid_metadata
    new_metadata["annotations"][0]["core:sample_start"] = 10000
    response = client.put(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file/path/meta',
        json=new_metadata,
    )
    assert response.status_code == 204
    response = client.get(
        f'/api/datasources/{test_datasource["account"]}/{test_datasource["container"]}/file/path/meta'
    )
    assert response.status_code == 200
    response_object = response.json()
    assert response_object["global"]["traceability:revision"] == 1
    assert (
        response_object["global"]["traceability:origin"]["account"]
        == test_datasource["account"]
    )
    assert (
        response_object["global"]["traceability:origin"]["container"]
        == test_datasource["container"]
    )
    assert response_object["global"]["traceability:origin"]["file_path"] == "file/path"
    assert response_object["annotations"][0]["core:sample_start"] == 10000
