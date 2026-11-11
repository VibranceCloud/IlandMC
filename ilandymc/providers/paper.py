from .base import Provider, Artifact


class PaperProvider(Provider):
    """Paper downloads provider using the supported Fill v3 REST API."""

    name = "paper"
    API = "https://fill.papermc.io/v3/projects/paper"

    async def versions(self):
        response = await self.client.get(self.API)
        response.raise_for_status()
        payload = response.json()
        grouped = payload.get("versions")
        if not isinstance(grouped, dict):
            raise ValueError("Paper downloads API returned an invalid versions document")
        # The service groups versions; preserve the service's newest-first ordering.
        return [version for group in grouped.values() for version in group]

    async def latest_artifact(self, version):
        response = await self.client.get(f"{self.API}/versions/{version}/builds")
        response.raise_for_status()
        builds = response.json()
        if not isinstance(builds, list):
            raise ValueError("Paper downloads API returned an invalid builds document")

        # Paper explicitly recommends stable builds for production. Do not silently
        # fall back to experimental builds when a stable one is unavailable.
        build = next((item for item in builds if item.get("channel") == "STABLE"), None)
        if build is None:
            raise ValueError(f"No stable Paper build available for Minecraft {version}")

        download = build.get("downloads", {}).get("server:default")
        if not isinstance(download, dict) or not download.get("url"):
            raise ValueError("Paper stable build has no server:default download")
        checksums = download.get("checksums") or {}
        checksum = checksums.get("sha256")
        return Artifact(
            software=self.name,
            minecraft_version=version,
            build=str(build["id"]),
            download_url=download["url"],
            checksum=checksum,
            checksum_algorithm="sha256" if checksum else None,
            filename=download.get("name") or "server.jar",
        )
