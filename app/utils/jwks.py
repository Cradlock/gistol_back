import httpx
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError


class TelegramJWKClient(PyJWKClient):
    def fetch_data(self):
        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
                response = client.get(self.uri)
                response.raise_for_status()
                jwk_set = response.json()
        except httpx.HTTPError as exc:
            raise PyJWKClientConnectionError(
                f'Fail to fetch data from the url, err: "{exc}"'
            ) from exc

        if self.jwk_set_cache is not None:
            self.jwk_set_cache.put(jwk_set)
        return jwk_set
