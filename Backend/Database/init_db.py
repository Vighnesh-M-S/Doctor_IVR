import asyncio
from db_setup import Base, Doctor
from database import async_engine, async_sessionmaker

async def init_db():
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert initial data
    async with async_sessionmaker() as session:
        result = await session.execute("""SELECT COUNT(*) FROM doctors""")
        count = result.scalar_one()

        if count == 0:
            cardiologists = [Doctor(name="Doctor. Smith", specialization="Cardiologist"),
                             Doctor(name="Doctor. Patel", specialization="Cardiologist")]
            dermatologists = [Doctor(name="Doctor. Khan", specialization="Dermatologist"),
                              Doctor(name="Doctor. Lee", specialization="Dermatologist")]
            orthopedics = [Doctor(name="Doctor. Davis", specialization="Orthopedic"),
                           Doctor(name="Doctor. Mehta", specialization="Orthopedic")]

            session.add_all(cardiologists + dermatologists + orthopedics)
            await session.commit()

if __name__ == "__main__":
    asyncio.run(init_db())
