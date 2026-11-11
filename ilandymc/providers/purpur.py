from .base import Provider, Artifact
class PurpurProvider(Provider):
    name="purpur"; API="https://api.purpurmc.org/v2/purpur"
    async def versions(self):
        r=await self.client.get(self.API); r.raise_for_status(); return r.json()["versions"]
    async def latest_artifact(self,version):
        r=await self.client.get(f"{self.API}/{version}"); r.raise_for_status()
        build=str(r.json()["builds"]["latest"])
        return Artifact(software=self.name,minecraft_version=version,build=build,
          download_url=f"{self.API}/{version}/{build}/download",filename="server.jar")
