from databases import Database as AsyncDatabase

from insurance_holder.model import Code, CodeConfig


class DatabaseService:
    def __init__(self,
                 client: AsyncDatabase,
                 ):
        self._client = client
