"""Make remote OpenViking resource additions idempotent for Hermes.

The upstream add_resource endpoint may finish parsing after the 30 second
client deadline. A retry with an automatic destination then creates a second
resource tree. This build patch gives each remote URL a deterministic target
and treats an existing target as an accepted asynchronous job.
"""

from pathlib import Path


TARGET = Path("/opt/hermes/plugins/memory/openviking/__init__.py")

OLD = '''            resp = self._client.post("/api/v1/resources", payload)
            result = resp.get("result", {})
'''

NEW = '''            target_uri = payload.get("to", "")
            if _is_remote_resource_source(url) and not target_uri and not payload.get("parent"):
                parsed_remote = urlparse(url)
                normalized_remote = parsed_remote._replace(fragment="").geturl()
                host = re.sub(r"[^a-z0-9]+", "-", (parsed_remote.hostname or "remote").lower()).strip("-")
                resource_id = uuid.uuid5(uuid.NAMESPACE_URL, normalized_remote).hex[:20]
                target_uri = f"viking://resources/web-{host[:48]}-{resource_id}"
                payload["to"] = target_uri
            if _is_remote_resource_source(url):
                payload["wait"] = False

            if target_uri:
                try:
                    self._client.get("/api/v1/fs/stat", params={"uri": target_uri}, timeout=5.0)
                    return json.dumps({
                        "status": "already_queued",
                        "root_uri": target_uri,
                        "message": "Resource already exists or is being processed. Do not retry it.",
                    }, ensure_ascii=False)
                except _OpenVikingHTTPError as existing_error:
                    if existing_error.status_code != 404:
                        raise

            try:
                resp = self._client.post("/api/v1/resources", payload)
                result = resp.get("result", {})
            except Exception as request_error:
                if not target_uri:
                    raise
                try:
                    self._client.get("/api/v1/fs/stat", params={"uri": target_uri}, timeout=5.0)
                except Exception:
                    raise request_error
                return json.dumps({
                    "status": "queued",
                    "root_uri": target_uri,
                    "message": "Resource was accepted and continues processing asynchronously. Do not retry it.",
                }, ensure_ascii=False)
'''


source = TARGET.read_text(encoding="utf-8")
if NEW in source:
    raise SystemExit(0)
if source.count(OLD) != 1:
    raise SystemExit("OpenViking resource tool patch target was not found exactly once")
TARGET.write_text(source.replace(OLD, NEW), encoding="utf-8")
