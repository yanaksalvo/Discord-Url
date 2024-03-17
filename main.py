import os
import aiohttp
import asyncio
import time

token = ""  # token
hook = ""  # webhook link
guild = "" # kendi sunucunuzun idsi
vanity_list = [""] # istediğiniz url
delay = 0.10
claimed = False

async def notify_start(vanity_code):
    embed = {
        "title": "Vanity Sniper Started",
        "description": f"Target Vanity Code: {vanity_code}",
        "color": 0000
    }
    payload = {
        "content": "@everyone",
        "embeds": [embed]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(hook, json=payload) as response:
            print(f"Sent start notification, status: {response.status}")

async def notify_vanity_claimed(vanity_code, elapsed_time):
    elapsed_time_ms = int(elapsed_time * 1000)
    vanity_url = f"[{vanity_code}](https://discord.gg/{vanity_code})"
    embed = {
        "title": "Vanity Claimed",
        "description": f"Vanity Code: {vanity_url} (çekildiği süre: {elapsed_time_ms} ms)\nGuild ID: {guild}",
        "color": 0000
    }
    payload = {
        "content": "@everyone",
        "embeds": [embed]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(hook, json=payload) as response:
            print(f"Sent claimed notification, status: {response.status}")

async def claim(session, url, json):
    global claimed
    if claimed:
        return
    claimed = True
    start_time = time.time()
    async with session.patch(url, json=json, headers={
        "Authorization": token,
        "X-Audit-Log-Reason": ":D",
        "Content-Type": "application/json"
    }) as response:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(response.status)
        if response.status in [200, 201]:
            print(f"[+] Vanity claimed: {json['code']}")
            await notify_vanity_claimed(json['code'], elapsed_time)
        else:
            print(f"[-] Failed to claim vanity: {json['code']} | status: {response.status}")

async def fetchVanity(session, vanity, x, semaphore):
    if not vanity:
        return
    try:
        async with session.get(f"https://canary.discord.com/api/v10/invites/{vanity}", headers={"Authorization": token}) as response:
            status = response.status
            if status == 404:
                await claim(session, f"https://canary.discord.com/api/v9/guilds/{guild}/vanity-url", {"code": vanity})
            elif status == 200:
                print(f"[+] Attempt: {x} | Vanity: {vanity}")
            elif status == 429:
                print("[-] | Rate Limited")
            else:
                print(f"[-] Unknown Error | Status: {status}")
                raise SystemExit
    except Exception as error:
        print(f"[-] | Error: {error}")
        await asyncio.sleep(delay)

async def threadExecutor(vanity, x):
    start_time = time.time()
    semaphore = asyncio.Semaphore(10)  
    async with aiohttp.ClientSession() as session:
        tasks = [fetchVanity(session, vanity, x, semaphore) for _ in range(10)] 
        await asyncio.gather(*tasks)
    end_time = time.time()
    elapsed_time = end_time - start_time
    elapsed_time_ms = int(elapsed_time * 1000)
    print(f"Vanity '{vanity}' çekildi. Geçen süre: {elapsed_time_ms} ms")

async def main():
    print("Starting...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://canary.discord.com/api/v9/users/@me", headers={"Authorization": token}) as response:
                if response.status in [200, 201, 204]:
                    user = await response.json()
                    id = user["id"]
                    username = user["username"]
                    print(f"Logged in as {username} | {id}")
                else:
                    print("[!] | Bad Auth")
                    raise SystemExit

                for vanity in vanity_list:
                    if claimed:
                        raise SystemExit
                    await notify_start(vanity)
                    for x in range(100000000):
                        if claimed:
                            break
                        await threadExecutor(vanity, x)
                        await asyncio.sleep(delay)

                print("[+] | Execution Completed")
        except Exception as error:
            print(f"[-] | Error: {error}")

asyncio.run(main())
