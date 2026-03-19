import time
from databases import Database

from insurance_holder.etc.enums import CodeType, CodeEffect, CountdownStatus
from insurance_holder.model import Countdown, CountdownState, StaticCode, CodeConfig
from insurance_holder.service.database.tables import COUNTDOWN_TABLE, COUNTDOWN_STATE_TABLE, CODE_CONFIG_TABLE


class CodeConfigRepository:
    """
    Database repository to operate on the code config table
    """

    def __init__(self, client: Database):
        self._client = client

    async def create(self,
                     code_config: CodeConfig,
                     countdown_id: str,
                     ):
        """
        Create a new code config
        :param code_config: The code config to create
        :param countdown_id: The countdown ID this code belongs to
        """
        payload = code_config.to_storage()
        payload['countdown_id'] = countdown_id

        query = CODE_CONFIG_TABLE.insert().values(**payload)
        await self._client.execute(query)

    async def get(self, code_config_id: int) -> CodeConfig | None:
        """
        Get a code config by its ID
        :param code_config_id: The ID of the code config to get
        :return: The code config with the given ID, or None if not found
        """
        query = CODE_CONFIG_TABLE.select().where(CODE_CONFIG_TABLE.c.id == code_config_id)
        record = await self._client.fetch_one(query)
        if not record:
            return None

        code_config = CodeConfig.from_storage(record)

        return code_config

    async def get_for_countdowns(self, countdown_ids: list[str]) -> list[tuple[str, CodeConfig]]:
        """
        Retrieve a list of code configs for multiple countdowns
        :param countdown_ids: A list of countdown IDs to retrieve code configs for
        :return: A list of tuples, where each tuple contains a countdown ID and its corresponding code config
        """
        query = CODE_CONFIG_TABLE.select().where(CODE_CONFIG_TABLE.c.countdown_id.in_(countdown_ids))
        records = await self._client.fetch_all(query)

        code_configs: list[tuple[str, CodeConfig]] = []
        for record in records:
            code_configs.append((record['countdown_id'], CodeConfig.from_storage(record)))

        return code_configs

    async def delete(self, code_config_id: int):
        """
        Delete a code config
        :param code_config_id: The ID of the code config to delete
        """
        query = CODE_CONFIG_TABLE.delete().where(CODE_CONFIG_TABLE.c.id == code_config_id)
        await self._client.execute(query)


class CountdownRepository:
    """
    Database repository to operate on the countdown table
    """

    def __init__(self, client: Database):
        self._client = client

    async def create(self, countdown: Countdown):
        """
        Create a new countdown
        :param countdown: The countdown to create
        """
        payload = countdown.to_storage()

        query = COUNTDOWN_TABLE.insert().values(**payload)
        await self._client.execute(query)

    async def list(self,
                   enabled: bool | None = None,
                   public: bool | None = None,
                   ) -> list[Countdown]:
        """
        List all countdowns in the database, optionally filtered by their properties
        :param enabled: Filter on `enabled` state. Leave as `None` to not filter on it
        :param public: Filter on `public` state. Leave as `None` to not filter on it
        :return: A list of countdowns matching the filters
        """
        query = COUNTDOWN_TABLE.select()

        if enabled is not None:
            query = query.where(COUNTDOWN_TABLE.c.enabled == enabled)
        if public is not None:
            query = query.where(COUNTDOWN_TABLE.c.public == public)

        records = await self._client.fetch_all(query)
        countdowns = [Countdown.from_storage(record) for record in records]

        return countdowns


class CountdownStateRepository:
    def __init__(self, client: Database):
        self._client = client

    async def create(self, countdown_state: CountdownState):
        payload = countdown_state.to_storage()

        query = COUNTDOWN_STATE_TABLE.insert().values(**payload)
        await self._client.execute(query)

    async def get_many(self, countdown_ids: list[str]) -> list[CountdownState]:
        query = COUNTDOWN_STATE_TABLE.select().where(COUNTDOWN_STATE_TABLE.c.id in countdown_ids)
        records = await self._client.fetch_all(query)

        countdown_states = []
        for record in records:
            countdown_state = CountdownState.from_storage(record)
            countdown_states.append(countdown_state)

        return countdown_states


class DatabaseService:
    def __init__(self,
                 client: Database,
                 ):
        self._client = client

        self._code_configs = CodeConfigRepository(client)
        self._countdowns = CountdownRepository(client)
        self._countdown_states = CountdownStateRepository(client)

    async def create_countdown(self,
                               countdown: Countdown,
                               first_run: int | None = None,
                               ):
        if not countdown.enabled:
            next_trigger_at = None
        elif first_run is not None:
            next_trigger_at = first_run
        else:
            next_trigger_at = int(time.time()) + countdown.countdown_time

        countdown_state = CountdownState(
            countdownId=countdown.countdown_id,
            publicStatus=None,
            status=CountdownStatus.HEALTHY if countdown.enabled else CountdownStatus.DISABLED,
            version=0,
            nextTriggerAt=next_trigger_at,
        )

        async with self._client.transaction():
            await self._countdowns.create(countdown)
            await self._countdown_states.create(countdown_state)

            for code_config in countdown.codes:
                await self._code_configs.create(code_config, countdown.countdown_id)

    async def list_countdown_states(self,
                                    enabled: bool | None = None,
                                    public: bool | None = None,
                                    ) -> list[tuple[Countdown, CountdownState]]:
        async with self._client.transaction():
            countdowns = await self._countdowns.list(enabled=enabled, public=public)
            codes = await self._code_configs.get_for_countdowns([countdown.countdown_id for countdown in countdowns])
            countdown_states = await self._countdown_states.get_many([countdown.countdown_id for countdown in countdowns])

        countdown_dict = {
            countdown.countdown_id: countdown for countdown in countdowns
        }

        for code in codes:
            countdown = countdown_dict.get(code[0])
            if countdown:
                countdown.codes.append(code[1])

        results: list[tuple[Countdown, CountdownState]] = []
        for countdown_state in countdown_states:
            results.append((countdown_dict[countdown_state.countdown_id], countdown_state))

        return results
