from .base import Provider, Artifact
class FabricProvider(Provider):
    name="fabric"; API="https://meta.fabricmc.net/v2"
    async def versions(self):
        r=await self.client.get(f"{self.API}/versions/game"); r.raise_for_status()
        return [x["version"] for x in r.json() if x.get("stable")]
    async def latest_artifact(self,version):
        r=await self.client.get(f"{self.API}/versions/loader/{version}"); r.raise_for_status()
        loaders=r.json()
        if not loaders: raise ValueError(f"No Fabric loader for {version}")
        loader=loaders[0]["loader"]["version"]
        installer=await self.client.get(f"{self.API}/versions/installer"); installer.raise_for_status()
        inst=installer.json()[0]["version"]
        url=f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader}/{inst}/server/jar"
        return Artifact(software=self.name,minecraft_version=version,build=loader,download_url=url,filename="server.jar")
