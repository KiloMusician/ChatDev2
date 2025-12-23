import asyncio
from temple_memory import retrieve_knowledge
from ship_state import ShipState
async def async_sync_data():
    """
    Asynchronously syncs data between Temple and Ship.
    """
    knowledge = retrieve_knowledge()
    ship = ShipState()
    if ship.health is not None:
        await asyncio.sleep(1)  # Simulate an I/O operation
        print("Data synced successfully.")
loop = asyncio.get_event_loop()
loop.run_until_complete(async_sync_data())