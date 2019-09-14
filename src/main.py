import aiohttp
import motor.motor_asyncio
from bs4 import BeautifulSoup


def main():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://mongodb:27017')
    db = client.db1

    print("✅ You have aiohttp installed")
    print("✅ You have BeautifulSoup4 installed")
    print("✅ You can access mongodb")

    print("You are Awesome! 👏🏼")


if __name__ == "__main__":
    main()
