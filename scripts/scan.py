import requests
from concurrent.futures import ThreadPoolExecutor
import re

SERVER_IP = "87.255.35.150"
START_PORT = 10000
END_PORT = 20000
TIMEOUT = 3
THREADS = 80

valid_streams = []

# Detect TS packets (start with 0x47 bytes)
def is_ts_stream(content):
    return content.startswith(b'\x47')

# Detect HLS playlist
def is_hls(content):
    return b"#EXTM3U" in content.split(b"\n")[0]

def scan_port(port):
    url = f"http://{SERVER_IP}:{port}"
    try:
        r = requests.get(url, timeout=TIMEOUT, stream=True)

        if r.status_code != 200:
            return None

        first_chunk = r.raw.read(512)

        # Check TS or HLS signature
        if is_ts_stream(first_chunk):
            print(f"[TS STREAM] {url}")
            return ("TS Stream", url)

        if is_hls(first_chunk):
            print(f"[HLS STREAM] {url}")
            return ("HLS Stream", url)

        # If response OK but unknown type
        print(f"[UNKNOWN STREAM] {url}")
        return ("Unknown Stream", url)

    except:
        return None

def main():
    print("Scanning ports... This may take time.\n")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        results = executor.map(scan_port, range(START_PORT, END_PORT + 1))

    streams = [s for s in results if s]

    # Save valid ports
    with open("valid_ports.txt", "w") as f:
        for stype, url in streams:
            f.write(f"{stype}: {url}\n")

    # Create M3U playlist
    with open("playlist.m3u", "w") as m:
        m.write("#EXTM3U\n")
        for idx, (stype, url) in enumerate(streams, start=1):
            m.write(f'#EXTINF:-1,{stype} {idx}\n{url}\n')

    print("\nScan complete!")
    print(f"Valid streams found: {len(streams)}")
    print("Saved to valid_ports.txt and playlist.m3u")

if __name__ == "__main__":
    main()
