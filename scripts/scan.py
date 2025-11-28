import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVER_IP = "87.255.35.150"
START_PORT = 10000
END_PORT = 20000

CONNECT_TIMEOUT = 2
READ_TIMEOUT = 2
THREADS = 40  # safer, prevents server blocking

def is_ts_stream(content):
    return content.startswith(b'\x47')

def is_hls(content):
    return content.startswith(b"#EXTM3U")

def scan_port(port):
    url = f"http://{SERVER_IP}:{port}"
    try:
        r = requests.get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), stream=True)

        if r.status_code != 200:
            return None

        chunk = r.raw.read(256)

        if is_ts_stream(chunk):
            print(f"[TS] {url}")
            return ("TS Stream", url)

        if is_hls(chunk):
            print(f"[HLS] {url}")
            return ("HLS Stream", url)

        print(f"[UNKNOWN] {url}")
        return ("Unknown Stream", url)

    except requests.exceptions.ConnectTimeout:
        return None
    except requests.exceptions.ReadTimeout:
        return None
    except requests.exceptions.RequestException:
        return None

def main():
    print("Starting full range scan...\n")

    results = []

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(scan_port, port): port for port in range(START_PORT, END_PORT + 1)}

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    # Save files
    with open("valid_ports.txt", "w") as f:
        for stype, url in results:
            f.write(f"{stype}: {url}\n")

    with open("playlist.m3u", "w") as m:
        m.write("#EXTM3U\n")
        for idx, (stype, url) in enumerate(results, start=1):
            m.write(f"#EXTINF:-1,{stype} {idx}\n{url}\n")

    print("\nScan completed!")
    print("Total valid streams:", len(results))

if __name__ == "__main__":
    main()
