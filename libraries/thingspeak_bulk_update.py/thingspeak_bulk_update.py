import requests

class Channel():
    def __init__(
        self,
        id,
        api_key=None,
        fmt="json",
        timeout=None,
        server_url="https://api.thingspeak.com",
    ):
        self.id = id
        self.api_key = api_key
        self.fmt = ("." + fmt) if fmt in ["json", "xml"] else ""
        self.timeout = timeout
        self.server_url = server_url

    # https://www.mathworks.com/help/thingspeak/bulkwritejsondata.html
    def bulk_update(self, data):
        if self.api_key is not None:
            data["write_api_key"] = self.api_key
        else:
            raise ValueError("Missing api_key")
        url = "{server_url}/channels/{id}/bulk_update{fmt}".format(
            server_url=self.server_url, id=self.id, fmt=self.fmt
        )
        r = requests.post(url, json=data, timeout=self.timeout)
        return self._fmt(r)
    
    def _fmt(self, r):
        r.raise_for_status()
        if self.fmt == "json":
            return r.json()
        else:
            return r.text