from .vanilla import VanillaProvider
from .paper import PaperProvider
from .purpur import PurpurProvider
from .fabric import FabricProvider

PROVIDERS={"vanilla":VanillaProvider,"paper":PaperProvider,"purpur":PurpurProvider,"fabric":FabricProvider}
def provider_for(name):
    try: return PROVIDERS[name.lower()]()
    except KeyError as exc: raise ValueError(f"Provider {name!r} is not currently supported") from exc
