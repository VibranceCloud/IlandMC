import httpx

class ModrinthClient:
    API="https://api.modrinth.com/v2"
    async def search(self,query,game_version=None,loaders=None,project_type="mod"):
        facets=[[f'project_type:{project_type}']]
        if game_version: facets.append([f'version:{game_version}'])
        if loaders:
            facets.append([f'categories:{x}' for x in loaders])
        params={"query":query,"facets":__import__("json").dumps(facets),"limit":20}
        async with httpx.AsyncClient(timeout=20,headers={"User-Agent":"IlandyMC/0.2.0 (server manager)"}) as c:
            r=await c.get(f"{self.API}/search",params=params); r.raise_for_status(); return r.json()["hits"]
    async def versions(self,project_id,game_version=None,loaders=None):
        params={}
        if game_version: params["game_versions"]=__import__("json").dumps([game_version])
        if loaders: params["loaders"]=__import__("json").dumps(loaders)
        async with httpx.AsyncClient(timeout=20) as c:
            r=await c.get(f"{self.API}/project/{project_id}/version",params=params); r.raise_for_status(); return r.json()
