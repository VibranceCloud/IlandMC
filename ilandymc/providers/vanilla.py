from .base import Provider, Artifact

class VanillaProvider(Provider):
    name="vanilla"
    MANIFEST="https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
    async def versions(self):
        r=await self.client.get(self.MANIFEST); r.raise_for_status()
        return [x["id"] for x in r.json()["versions"] if x.get("type") == "release"]
    async def latest_artifact(self,version):
        r=await self.client.get(self.MANIFEST); r.raise_for_status()
        item=next((x for x in r.json()["versions"] if x["id"]==version),None)
        if not item: raise ValueError(f"Unknown Minecraft version {version}")
        meta=await self.client.get(item["url"]); meta.raise_for_status()
        server=meta.json().get("downloads",{}).get("server")
        if not server: raise ValueError("Official manifest has no server artifact for this version")
        return Artifact(software=self.name,minecraft_version=version,build="release",
          download_url=server["url"],checksum=server.get("sha1"),checksum_algorithm="sha1",filename="server.jar")
